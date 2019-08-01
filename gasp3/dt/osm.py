"""
Methods to extract OSM data from the internet
"""


def download_by_boundary(input_boundary, output_osm, epsg,
                         GetUrl=True):
    """
    Download data from OSM using a bounding box
    """
    
    import os
    from osgeo         import ogr
    from gasp3.web.ff  import get_file
    from gasp3.pyt.oss import get_fileformat, get_filename
    
    if type(input_boundary) == dict:
        if 'top' in input_boundary and 'bottom' in input_boundary \
            and 'left' in input_boundary and 'right' in input_boundary:
            
            left, right, bottom, top = (
                input_boundary['left'], input_boundary['right'],
                input_boundary['bottom'], input_boundary['top']
            )
        
        else:
            raise ValueError((
                'input_boundary is a dict but the keys are not correct. '
                'Please use left, right, top and bottom as keys'
            ))
    
    elif type(input_boundary) == list:
        if len(input_boundary) == 4:
            left, right, bottom, top = input_boundary
        
        else:
            raise ValueError((
                'input boundary is a list with more than 4 objects. '
                'The list should be like: '
                'l = [left, right, bottom, top]'
            ))
    
    elif type(input_boundary) == ogr.Geometry:
        # Check if we have a polygon
        geom_name = input_boundary.GetGeometryName()
        
        if geom_name == 'POLYGON' or geom_name == 'MULTIPOLYGON':
            # Get polygon extent
            left, right, bottom, top = input_boundary.GetEnvelope()
        
        else:
            raise ValueError((
                'Your boundary is a non POLYGON ogr Geometry '
            ))
    
    else:
        # Assuming input boundary is a file
        
        #Check if file exists
        if not os.path.exists(input_boundary):
            raise ValueError((
                "Sorry, but the file {} does not exist inside the folder {}!"
            ).format(
                os.path.basename(input_boundary), os.path.dirname(input_boundary)
            ))
        
        # Check if is a raster
        from gasp3.gt.prop.ff import check_isRaster
        isRst = check_isRaster(input_boundary)
        
        if isRst:
            from gasp3.gt.prop.rst import rst_ext
            
            # Get raster extent
            left, right, bottom, top = rst_ext(input_boundary)
        
        else:
            from gasp3.gt.prop.feat import feat_count, get_ext
        
            # Check number of features
            number_feat = feat_count(input_boundary, gisApi='ogr')
            if number_feat != 1:
                raise ValueError((
                    'Your boundary has more than one feature. '
                    'Only feature classes with one feature are allowed.'
                ))
    
            # Get boundary extent
            left, right, bottom, top = get_ext(input_boundary)
    
    if epsg != 4326:
        from gasp3.dt.to.geom import create_point
        from gasp3.gt.mng.prj import project_geom
        
        bottom_left = project_geom(
            create_point(left, bottom), epsg, 4326, api='ogr'
        )
        
        top_right   = project_geom(
            create_point(right, top), epsg, 4326, api='ogr'
        )
        
        left , bottom = bottom_left.GetX(), bottom_left.GetY()
        right, top    = top_right.GetX()  , top_right.GetY()
    
    bbox_str = ','.join([str(left), str(bottom), str(right), str(top)])
    
    url = "https://overpass-api.de/api/map?bbox={box}".format(box=bbox_str)
    
    if GetUrl:
        return url
    
    if get_fileformat(output_osm) != '.xml':
        output_osm = os.path.join(
            os.path.dirname(output_osm),
            get_filename(output_osm) + '.xml')
    
    osm_file = get_file(url, output_osm)
    
    return output_osm


def download_by_psqlext(psqlCon, table, geomCol, outfile):
    """
    Download OSM file using extent in PGTABLE
    """
    
    from gasp3.sql.i  import tbl_ext
    from gasp3.web.ff import get_file
    
    ext = tbl_ext(psqlCon, table, geomCol)
    
    bbox_str = ",".join([str(x) for x in ext])
    
    url = "https://overpass-api.de/api/map?bbox={}".format(
        bbox_str
    )
    
    output = get_file(url, outfile)
    
    return output

