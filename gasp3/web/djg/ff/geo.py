"""
Deal with GeoData inside Django App
"""

def generate_json_asset_from_shapefile(rqst, field_tag, epsg_field, storing):
    """
    Receive a Geom file (ESRI Shapefile or others) from a form field
    
    store the file in the server and generate a json to be used in leaflet
    """
    
    import os
    from gasp3.web.djg.ff import save_file
    from gasp3.dt.to.shp  import shp_to_shp
    from gasp3.gt.mng.prj import project
    
    files = rqst.FILES.getlist(field_tag)
    
    for f in files:
        save_file(storing, f)
    
    if len(files) > 1:
        shape = os.path.join(
            storing,
            '{f_name}.shp'.format(
                f_name = os.path.splitext(files[0].name)[0]
            )
        )
    
    else:
        shape = os.path.join(storing, files[0].name)
    
    """TODO: See if the file format is in the GDAL drivers list"""
    
    # Boundary to json
    if int(str(rqst.POST[epsg_field])) != 4326:
        shp = os.path.join(
            os.path.dirname(str(shape)), 'wgs_shape.shp'
        )
        
        project(
            str(shape), shp, 4326,
            inEPSG=int(str(rqst.POST[epsg_field])), gisApi='ogr'
        )
    
    else:
        shp = str(shape)
    
    if os.path.splitext(os.path.basename(shp))[1] != '.json':
        bound_asset = os.path.join(storing, 'wgs_shape.json')
        
        shp_to_shp(shp, bound_asset, gisApi='ogr')
    
    else:
        bound_asset = shp
    
    return bound_asset, shape


def save_geodata(request, field_tag, folder):
    """
    Receive a file with vectorial geometry from a form field:
    
    Store the file in the server
    
    IMPORTANT: this method will only work if the FORM that is receiving the 
    files allows multiple files
    """
    
    import os
    from gasp3.web.djg.ff import save_file
    
    files = request.FILES.getlist(field_tag)
    
    for f in files:
        save_file(folder, f)
    
    if len(files) > 1:
        shape = os.path.join(folder, '{f_name}.shp'.format(
            f_name = os.path.splitext(files[0].name)[0]
        ))
    
    else:
        shape = os.path.join(folder, files[0].name)
    
    return shape

