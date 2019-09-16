"""
Google Maps Directions API methods to do things
related with network analysis
"""

from gasp3.pyt.web import json_fm_httpget

from . import select_api_key
from . import record_api_utilization

# ------------------------------ #
"""
Global Variables
"""
GOOGLE_GEOCODING_URL = 'https://maps.googleapis.com/maps/api/directions/json?'
# ------------------------------ #


def point_to_point(latA, lngA, latB, lngB, mode="driving"):
    """
    Go from A to B with Google Maps Directions API
    
    DRIVING OPTIONS: driving; walking; bicycling
    """
    
    import polyline
    
    # Get Key to be used
    KEY_FID, GOOGLE_API_KEY, NR_REQUESTS = select_api_key()
    
    path = json_fm_httpget((
        '{url}origin={lat},{lng}&'
        'destination={__lat},{__lng}&'
        'key={k}'
    ).format(
        url=GOOGLE_GEOCODING_URL, lat=str(latA), lng=str(lngA),
        __lat=str(latB), __lng=str(lngB), k=GOOGLE_API_KEY
    ))
    
    # Record api utilization
    record_api_utilization(KEY_FID, NR_REQUESTS + 1)
    
    results = path['routes'][0]
    
    results['polyline'] = polyline.decode(
        results['overview_polyline']['points']
    )
    
    results['general_distance'] = results['legs'][0]['distance']
    results['general_duration'] = results['legs'][0]['duration']
    
    del results['overview_polyline']['points']
    del results['legs'][0]['distance']
    del results['legs'][0]['duration']
    
    return results


def pnt_to_pnt_duration(latA, lngA, latB, lngB, mode="driving"):
    """
    Return duration from going from A to B
    
    DRIVING OPTIONS: driving; walking; bicycling
    """
    
    # Get Key to be used
    KEY_FID, GOOGLE_API_KEY, NR_REQUESTS = select_api_key()
    
    path = json_fm_httpget((
        '{url}origin={lat},{lng}&'
        'destination={__lat},{__lng}&'
        'key={k}'
    ).format(
        url=GOOGLE_GEOCODING_URL, lat=str(latA), lng=str(lngA),
        __lat=str(latB), __lng=str(lngB), k=GOOGLE_API_KEY
    ))
    
    # Record api utilization
    record_api_utilization(KEY_FID, NR_REQUESTS + 1)
    
    # Return result
    return path["routes"][0]["legs"][0]["duration"]["value"]


def get_time_pnt_destinations(origin, destinations):
    """
    Return the time needed to go from the origin to the nearest destination
    
    origin = Point Geometry
    destinations = list of dicts with the following structure
    {id: value, x: value, y: value}
    """
    
    for i in range(len(destinations)):
        dist_path = point_to_point(
            origin.GetY(), origin.GetX(),
            destinations[i]['y'], destinations[i]['x']
        )
        
        if not i:
            __id = destinations[i]['id']
            duration = dist_path['general_duration']
            distance = dist_path['general_distance']
        
        else:
            if dist_path['general_duration']['value'] < duration['value']:
                __id = destinations[i]['id']
                duration = dist_path['general_duration']
                distance = dist_path['general_distance']
    
    return __id, duration, distance

