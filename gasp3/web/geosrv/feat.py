"""
Use Geoserver inside a Django Application
"""


def get_feature_info(request, workspace, layer):
    """
    Geoserver getFeatureInfo data to a Json Response
    """
    
    import requests
    from django.http import JsonResponse
    
    url = (
        'http://localhost:8888/geoserver/wms?&'
        'INFO_FORMAT=application/json&'
        'REQUEST=GetFeatureInfo&'
        'EXCEPTIONS=application/vnd.ogc.se_xml&'
        'SERVICE=WMS&VERSION=1.1.1&'
        'WIDTH={width}&HEIGHT={height}&'
        'X={x}&Y={y}&'
        'BBOX={bbox}&'
        'LAYERS={work}:{lyr}&'
        'QUERY_LAYERS={work}:{lyr}&'
        'TYPENAME={work}:{lyr}&'
        'CRS=EPSG:4326'
    ).format(
        work=workspace, lyr=layer,
        width=request.GET['WIDTH'], height=request.GET['HEIGHT'],
        x=request.GET['X'], y=request.GET['Y'],
        bbox=request.GET['BBOX']
    )
    
    r = requests.get(
        url, headers={'Accept': 'application/json'}
    )
    
    json_data = r.json()
    
    return JsonResponse(json_data)

