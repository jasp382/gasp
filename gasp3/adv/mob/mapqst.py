"""
MapQuest API
"""

MAIN_URL = "http://www.mapquestapi.com/"
OPEN_URL = "http://open.mapquestapi.com/"
API_KEY  = "AiVWEixu0ucZ6D7GXcIUcIGumzcYClDd"


def matrix_route(locations, option="allToAll", keyToUse=None,
                 useOpen=True):
    """
    Matrix Route POST Service
    
    locations = [
        {
            "latLng" : {"lat" : XXX, "lng" : XXX}
        },
        ...
    ]
    
    options:
    * allToAll
    * manyToOne
    * oneToMany
    """
    
    from gasp3.pyt.web import data_from_post
    
    KEY_TO_USE = API_KEY if not keyToUse else keyToUse
    URL_TO_USE = MAIN_URL if not useOpen else OPEN_URL
    
    OPTIONS = {
        "allToAll" : False, "manyToOne" : False
    } if option == "oneToMany" else {option : True}
    
    URL = "{}directions/v2/routematrix?key={}".format(URL_TO_USE, KEY_TO_USE)
    
    data = data_from_post(URL, {
        "locations" : locations,
        "options"   : OPTIONS
    })
    
    return data



def rev_geocode(lat, lng, keyToUse=None, useOpen=None):
    """
    Use Reverse Geocoding Service of MapQuest
    """
    
    from gasp3.pyt.web import data_from_post
    
    KEY_TO_USE = API_KEY if not keyToUse else keyToUse
    URL_TO_USE = MAIN_URL if not useOpen else OPEN_URL
    
    URL = "{}geocoding/v1/reverse?key={}".format(URL_TO_USE, KEY_TO_USE)
    
    data = data_from_post(URL, {
        "location" : {"latLng" : {"lat" : lat, "lng" : lng}}
    })
    
    return data

