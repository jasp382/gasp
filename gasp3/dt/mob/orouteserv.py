"""
Open Route Service tools
"""

import os

API_KEY  = '58d904a497c67e00015b45fc5867ec0c09d74a4e92d06213a4937aca'
MAIN_URL = 'https://api.openrouteservice.org/'


APIS_DB = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'apis.db3'
)


def get_keys():
    """
    Return available keys for this API
    """
    
    from gasp.fm.sql import query_to_df
    
    keys = sqlq_to_df(APIS_DB, (
        "SELECT fid, key, date, nrqst FROM openrouteservice "
        "ORDER BY fid"
    ), db_api='sqlite')
    
    return keys


def directions(latOrigin, lngOrigin, latDestination, lngDestination,
               modeTransportation='foot-walking'):
    """
    Get Shortest path between two points using Directions service
    
    profile options:
    * driving-car;
    * driving-hgv;
    * cycling-regular;
    * cycling-road;
    * cycling-safe;
    * cycling-mountain;
    * cycling-tour;
    * cycling-electric;
    * foot-walking;
    * foot-hiking;
    * wheelchair.
    
    preference options:
    * fastest, shortest, recommended
    
    format options: geojson, gpx
    
    DOC: https://openrouteservice.org/documentation/#/authentication/UserSecurity
    """
    
    from gasp.web import json_fm_httpget
    
    URL = (
        "{_url_}directions?api_key={apik}&"
        "coordinates={ox},{oy}|{dx},{dy},&"
        "profile={prof}&preferences=fastest&"
        "format=geojson"
    ).format(
        _url_=MAIN_URL, apik=API_KEY,
        oy=latOrigin, ox=lngOrigin, dy=latDestination, dx=lngDestination,
        prof=modeTransportation
    )
    
    data = json_fm_httpget(URL)
    
    return data


def isochrones(locations, range, range_type='time',
               modeTransportation='foot-walking',
               intervals=None, useKey=None):
    """
    Obtain areas of reachability from given locations
    
    The Isochrone Service supports time and distance analyses for one
    single or multiple locations. You may also specify the isochrone
    interval or provide multiple exact isochrone range values.
    This service allows the same range of profile options listed in the
    ORS Routing section which help you to further customize your request
    to obtain a more detailed reachability area response.
    """
    
    from gasp.web import json_fm_httpget
    
    url_intervals = "&interval={}".format(str(intervals)) if intervals \
        else ""
    
    API_KEY_TO_USE = API_KEY if not useKey else useKey
    
    URL = (
        "{_url_}isochrones?api_key={apik}&"
        "locations={loc}&profile={transport}&range_type={rng_type}&"
        "range={rng}{_int}"
    ).format(
        _url_=MAIN_URL, apik=API_KEY_TO_USE,
        loc=locations, transport=modeTransportation,
        rng_type=range_type, rng=range,
        _int=url_intervals
    )
    
    data = json_fm_httpget(URL)
    
    return data

def isochrones_to_file(locations, range, outFile,
               modeTransportation='foot-walking',
               intervals=None, range_type='time'):
    
    import json
    
    data = isochrones(
        locations, range, range_type,
        modeTransportation=modeTransportation,
        intervals=intervals
    )
    
    with open(outFile, 'w') as j:
        json.dump(data, j)
    
    return outFile


def matrix_od(locations, idxSources="all", idxDestinations="all",
              useKey=None, modeTransportation='foot-walking'):
    """
    Execute Matrix Service
    """
    
    from gasp.web import json_fm_httpget
    
    API_KEY_TO_USE = API_KEY if not useKey else useKey
    
    URL = (
        "{_main}matrix?api_key={apik}&profile={transport}&"
        "locations={locStr}&sources={idx_src}&destinations={idx_des}"
        "&metrics=duration&units=m&optimized=true"
    ).format(
        _main=MAIN_URL, apik=API_KEY_TO_USE,
        transport=modeTransportation, locStr=locations,
        idx_src=idxSources, idx_des=idxDestinations
    )
    
    data = json_fm_httpget(URL)
    
    return data

