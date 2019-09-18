"""
Google Maps Geocoding API Endpoints
"""

from gasp3.pyt.web import http_to_json

from . import select_api_key
from . import record_api_utilization
from . import check_result

# ------------------------------ #
"""
Global Variables
"""
GOOGLE_GEOCODING_URL = 'https://maps.googleapis.com/maps/api/geocode/json?'
# ------------------------------ #


def get_position(address, country=None, language=None, locality=None,
                 postal_code=None):
    """
    Get position of an address
    
    * Address examples
    address = ['1600 Amphitheatre+Parkway', 'Mountain+View', 'CA']
    address = 'Rua dos Combatentes da Grande Guerra 14,3030-175,Coimbra'
    
    Only one address is allowed
    """
    
    ADDRESS_SANITIZE = ','.join(address) if \
        type(address) == list else address if \
        type(address) == str else None
    
    if not ADDRESS_SANITIZE:
        raise ValueError(('Given Address is not valid!'))
    
    ADDRESS_SANITIZE = ADDRESS_SANITIZE if ' ' not in ADDRESS_SANITIZE \
        else ADDRESS_SANITIZE.replace(' ', '+')
        
    COUNTRY  = '' if not country else 'country:{}'.format(country)
    LOCALITY = '' if not locality else 'locality:{}'.format(locality)
    POS_CODE = '' if not postal_code else 'postal_code:{}'.format(postal_code)
    
    if COUNTRY != '' or LOCALITY != '' or POS_CODE != '':
        COMPONENTS = '&components={}'.format(
            '|'.join([x for x in [COUNTRY, LOCALITY, POS_CODE] if x != ''])
        )
    
    else: COMPONENTS = ''
    
    LANGUAGE = '' if not language else '&language={}'.format(language)
    
    # Get Key to be used
    KEY_FID, GOOGLE_API_KEY, NR_REQUESTS = select_api_key()
    
    URL = '{url}address={addrs}&key={k}{lang}{comp}'.format(
        url=GOOGLE_GEOCODING_URL, k=GOOGLE_API_KEY,
        addrs=ADDRESS_SANITIZE,
        lang=LANGUAGE,
        comp=COMPONENTS
    )
    
    # Record api utilization
    record_api_utilization(KEY_FID, NR_REQUESTS + 1)
    
    try:
        position = http_to_json(URL)
    except:
        raise ValueError(
            'Something went wrong. The URL was {}'.format(URL)
        )
    
    return check_result(position, "GEOCODING")


def get_address(lat, lng):
    """
    Get a address for a given point
    """
    
    def sanitize_coord(coord):
        if ',' in str(coord):
            return str(coord).replace(',', '.')
        
        else:
            return str(coord)
    
    # Get Key to be used
    KEY_FID, GOOGLE_API_KEY, NR_REQUESTS = select_api_key()
    
    URL = '{url}latlng={__lat},{__long}&key={k}'.format(
        url    = GOOGLE_GEOCODING_URL,
        k      = GOOGLE_API_KEY,
        __lat  = sanitize_coord(lat),
        __long = sanitize_coord(lng)
    )
    
    # Record api utilization
    record_api_utilization(KEY_FID, NR_REQUESTS + 1)
    
    try:
        address = http_to_json(URL)
    except:
        raise ValueError(
            'Something went wrong. The URL was {}'.format(URL)
        )
    
    return check_result(address, "GEOCODING")

