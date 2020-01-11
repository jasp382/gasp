"""
Methods to extract OSM data from the internet
"""


def download_by_boundary(input_boundary, folder_out, osm_name, epsg,
                         GetUrl=True, conPSQL=None, geomCol=None,
                         justOneFeature=None):
    """
    Download data from OSM using a bounding box
    """
    
    import os
    from osgeo        import ogr
    from gasp.web.ff  import get_file
    from gasp.pyt.oss import get_fileformat, get_filename
    from gasp.pyt.oss import os_name
    
    OS_NAME = os_name()
    
    EXTENTS = []
    
    if conPSQL and geomCol:
        """
        Assuming input_boundary is a PostgreSQL Table
        """
        
        from gasp.pyt   import obj_to_lst
        from gasp.sql.i import tbl_ext
        
        for t in obj_to_lst(input_boundary):
            EXTENTS.append(tbl_ext(conPSQL, t, geomCol))
    
    else:
        if type(input_boundary) == dict:
            if 'top' in input_boundary and 'bottom' in input_boundary \
                and 'left' in input_boundary and 'right' in input_boundary:
                
                EXTENTS.append([
                    input_boundary['left'],input_boundary['right'],
                    input_boundary['bottom'], input_boundary['top']
                ])
        
            else:
                raise ValueError((
                    'input_boundary is a dict but the keys are not correct. '
                    'Please use left, right, top and bottom as keys'
                ))
    
        elif type(input_boundary) == list:
            if len(input_boundary) == 4:
                EXTENTS.append(input_boundary)
        
            else:
                raise ValueError((
                    'input boundary is a list with more than 4 objects. '
                    'The list should be like: '
                    'l = [left, right, bottom, top]'
                ))
    
        elif type(input_boundary) == ogr.Geometry:
            EXTENTS.append(input_boundary.GetEnvelope())
    
        else:
            # Assuming input boundary is a file
        
            #Check if file exists
            if not os.path.exists(input_boundary):
                raise ValueError((
                    "Sorry, but the file {} does not exist inside the folder {}!"
                ).format(
                    os.path.basename(input_boundary),
                    os.path.dirname(input_boundary)
                ))
        
            # Check if is a raster
            from gasp.gt.prop.ff import check_isRaster
            isRst = check_isRaster(input_boundary)
        
            # Get EPSG
            if not epsg:
                from gasp.gt.prop.prj import get_epsg
            
                epsg = get_epsg(input_boundary)
        
            if isRst:
                from gasp.gt.prop.rst import rst_ext
            
                # Get raster extent
                EXTENTS.append(rst_ext(input_boundary))
        
            else:
                from gasp.gt.prop.ff import drv_name
                
                # Todo: check if it is shape
                
                # Open Dataset
                inSrc = ogr.GetDriverByName(drv_name(
                    input_boundary)).Open(input_boundary)
                
                lyr = inSrc.GetLayer()
                
                i = 1
                for feat in lyr:
                    geom = feat.GetGeometryRef()
                    
                    featext = geom.GetEnvelope()
                    
                    EXTENTS.append(featext)
                    
                    if justOneFeature:
                        break
    
    if epsg != 4326:
        from gasp.gt.to.geom import new_pnt
        from gasp.gt.prj     import proj
        
        for i in range(len(EXTENTS)):
            bottom_left = proj(new_pnt(EXTENTS[i][0], EXTENTS[i][2]), None,
                               4326, inEPSG=epsg, gisApi='OGRGeom')
        
            top_right   = proj(new_pnt(EXTENTS[i][1], EXTENTS[i][3]), None,
                               4326, inEPSG=epsg, gisApi='OGRGeom')
        
            left , bottom = bottom_left.GetX(), bottom_left.GetY()
            right, top    = top_right.GetX()  , top_right.GetY()
            
            EXTENTS[i] = [left, right, bottom, top]
    
    url = "https://overpass-api.de/api/map?bbox={}"
    
    RESULTS = []
    for e in range(len(EXTENTS)):
        bbox_str = ','.join([str(p) for p in EXTENTS[e]])
        
        if GetUrl:
            RESULTS.append(url.format(bbox_str))
            continue
        
        if len(EXTENTS) == 1:
            outOsm = os.path.join(folder_out, osm_name + '.xml')
        else:
            outOsm = os.path.join(folder_out, "{}_{}.xml".format(osm_name, str(e)))
        
        osm_file = get_file(
            url.format(bbox_str), outOsm,
            useWget=None if OS_NAME == 'Windows' else None
        )
        
        RESULTS.append(osm_file)
    
    return RESULTS[0] if len(RESULTS) == 1 else RESULTS


def osm_extraction(boundary, osmdata, wepsg, output):
    """
    Extract OSM Data from a xml file with osmosis
    
    The extraction is done using the extent of a boundary
    """
    
    import os
    from osgeo           import ogr
    from gasp            import exec_cmd
    from gasp.gt.prop.ff import drv_name
    from gasp.gt.prj     import proj
    
    # Assuming that boundary has only one feature
    # Get Geometry
    dtSrc = ogr.GetDriverByName(drv_name(boundary)).Open(boundary)
    lyr   = dtSrc.GetLayer()
    
    if os.path.isdir(output):
        from gasp.pyt.oss import get_filename
        
        geoms    = []
        outFiles = []
        
        name_out = get_filename(osmdata)
        for feat in lyr:
            geoms.append(feat.GetGeometryRef())
            
            outFiles.append(os.path.join(output, "{}_{}.xml".format(
                name_out, str(feat.GetFID())
            )))
        
    else:
        for feat in lyr:
            geoms = [feat.GetGeometryRef()]
            break
        
        outFiles = [output]
    
    for g in range(len(geoms)):
        # Convert boundary to WGS84 -EPSG 4326
        geom_wgs = proj(
            geoms[g], None, 4326, inEPSG=int(wepsg), gisApi='OGRGeom'
        ) if int(wepsg) != 4326 else geoms[g]
    
        # Get boundary extent
        left, right, bottom, top = geom_wgs.GetEnvelope()
    
        # Osmosis shell comand
        osmExt = os.path.splitext(osmdata)[1]
        osm_f  = 'enableDateParsing=no' \
            if osmExt == '.xml' or osmExt == '.osm' else ''
    
        cmd = (
            'osmosis --read-{_f} {p} file={_in} --bounding-box top={t} left={l}'
            ' bottom={b} right={r} --write-{outext} file={_out}'
        ).format(
            _f = 'xml' if osmExt == '.xml' or osmExt == '.osm' else 'pbf',
            p = osm_f, _in = osmdata,
            t = str(top), l = str(left), b = str(bottom), r = str(right),
            _out = outFiles[g], outext=os.path.splitext(outFiles[g])[1][1:]
        )
    
        # Execute command
        outcmd = exec_cmd(cmd)
    
    return output


