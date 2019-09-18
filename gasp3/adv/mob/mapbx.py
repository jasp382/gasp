"""
Mapbox API
"""

import os

MAIN_URL = "https://api.mapbox.com/"
API_KEY  = ("pk.eyJ1IjoiZ2lzc2VucHkiLCJhIjoiY2psZ3hhb"
            "2c4MHBtcjNwdXg5aXNneTg0ZyJ9.ZvYEQiA0QgQT"
            "WOgG6GXLxQ")

APIS_DB = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'apis.db3'
)

def get_keys():
    """
    Return available keys for this API
    """
    
    from gasp3.sql.fm import Q_to_df
    
    keys = sqlq_to_df(APIS_DB, (
        "SELECT fid, key, date, nrqst FROM mapbox "
        "ORDER BY fid"
    ), db_api='sqlite')
    
    return keys


def matrix(locations, idxSources="all", idxDestinations="all",
           useKey=None, modeTransportation='driving'):
    """
    modeTransportation Options:
    * driving;
    * walking;
    * cycling;
    * driving-traffic.
    """
    
    from gasp3.pyt.web import http_to_json
    
    API_KEY_TO_USE = API_KEY if not useKey else useKey
    
    URL = (
        "{murl}directions-matrix/v1/mapbox/{mtrans}/{coord}?"
        "sources={srcIdx}&destinations={desIdx}&access_token="
        "{api_key}"
    ).format(
        murl=MAIN_URL, mtrans=modeTransportation,
        coord=locations, srcIdx=idxSources, desIdx=idxDestinations,
        api_key=API_KEY_TO_USE
    )
    
    data = http_to_json(URL)
    
    return data

