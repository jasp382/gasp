"""
Retrieve data drawed with leaflet draw
"""


def get_boundary(rqst, geo_field, epsg_field, storing):
    """
    Receive a form field with a string with five points...
    Create a shapefile from that...
    
    The input is the request object with POST Data and the key to access
    geographic information
    
    Returns json asset (to be used in leaflet) and shapefile on the epsg
    given by the user in the form
    """
    
    import os;            import json
    from gasp3.gt.to.shp  import shp_to_shp
    from gasp3.gt.prj     import proj
    
    # Get Json file in 4326 - default for leaflet
    bounds = str(rqst.POST[geo_field])
    b = []
    
    for pnt in bounds.split(';'):
        x, y = pnt.split(',')
        b.append([float(x), float(y)])
    
    geo_json_boundary = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"Id": 0},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [b]
                }
            }
        ]
    }
    
    bound_asset = os.path.join(storing, 'wgs_shape.json')
    
    with open(bound_asset, mode="w") as outjson:
        json.dump(geo_json_boundary, outjson)
        outjson.close()
    
    # Json to ESRI Shapefile in 4326
    shape_wgs = os.path.join(storing, 'wgs_shape.shp')
    
    shp_to_shp(bound_asset, shape_wgs, gisApi='ogr')
    
    if epsg_field:
        shape = proj(
            shape_wgs, os.path.join(storing, 'lmt.shp'),
            int(str(rqst.POST[epsg_field])),
            inEPSG=4326, gisApi='ogr'
        ) 
    
    else:
        shape = shape_wgs
    
    return bound_asset, shape


def get_circle_dimensions(rqst, circle_field):
    """
    Receive a form field with a string with the lat/long and radius of a 
    buffer drawed by the user. Return these elements as:
    
    {
        y: value,
        x: value,
        r: value
    }
    """
    
    lat_lng, radius = str(rqst.POST[circle_field]).split(';')
    lat, lng = lat_lng.split(',')
    
    return {
        'y' : lat, 'x' : lng, 'r': radius
    }


def get_circle(rqst, buffer_field, storing, epsg_field=None, epsg_code=None):
    """
    Receive a form field with a string with the lat/long and radius of a 
    buffer drawed by the user.
    
    Create a shapefile from that...
    
    The input is the request object with POST Data and the key to access
    geographic information
    
    Returns json asset (to be used in leaflet) and shapefile on the epsg
    given by the user in the form
    """
    
    import os; from osgeo   import ogr
    from gasp3.gt.prj       import proj
    from gasp3.gt.anls.prox import ogr_buffer
    from gasp3.gt.to.geom   import new_pnt
    from gasp3.gt.to.shp    import shp_to_shp
    
    # Create a buffer with form data
    lat_lng, radius = str(rqst.POST[buffer_field]).split(';')
    lat, lng = lat_lng.split(',')
    
    buffer_3857 = os.path.join(storing, 'buffer_shp.shp')
    
    pnt_3857 = proj(
        new_pnt(float(lng), float(lat)), None,
        3857, inEPSG=4326, gisApi='OGRGeom'
    )
    ogr_buffer([pnt_3857], float(radius), buffer_3857)
    
    # Convert to json
    buffer_wgs = proj(
        buffer_3857,
        os.path.join(storing, 'buffer_4326.shp'),
        4326, inEPSG=3857, gisApi='ogr'
    ); buffer_json = shp_to_shp(
        buffer_wgs, os.path.join(storing, 'inbuffer.json'),
        gisApi='ogr'
    )
    
    if epsg_code or epsg_field:
        if epsg_code and not epsg_field:
            epsg = int(epsg_code)
        elif not epsg_code and epsg_field:
            epsg = int(rqst.POST[epsg_field])
        elif epsg_code and epsg_field:
            epsg = int(rqst.POST[epsg_field])
        
        if epsg != 3857 and epsg != 4326:
            return_buffer = proj(
                buffer_3857, os.path.join(
                    storing, 'buffer_{}.shp'.format(str(epsg))),
                epsg, inEPSG=3857, gisApi='ogr'
            )
        
        elif epsg != 3857 and epsg == 4326:
            return_buffer = buffer_wgs
        
        else:
            return_buffer = buffer_3857
    
    else:
        return_buffer = buffer_3857
    
    return buffer_json, return_buffer

