"""
API's subpackage:

Tools to extract data from Google using Google Maps API's Endpoints
"""

import datetime
import os

# Google
#GOOGLE_API_KEY = 'AIzaSyAmyPmqtxD20urqtpCpn4ER74a6J4N403k'
#GOOGLE_API_KEY = 'AIzaSyAxfyLSrj4WTboVipv9Faglk9znAKtwAnY'
# TRN
#GOOGLE_API_KEY = 'AIzaSyBTDoFnabhVEULsstwvIDB6XE9djyzzHsE'
# GIS-SENPY-1
#GOOGLE_API_KEY = 'AIzaSyCwlklT_QloDUIB-awJhBIHPNhkdmy14OI'
# GIS-SENPY-2
#GOOGLE_API_KEY = 'AIzaSyAIyhmiacy98icdyQReraTq8hlcsKdxA0Y'
# GIS-SENPY-3
#GOOGLE_API_KEY = 'AIzaSyDjepvLEDBJlPCLR1L3Lguf5Ry2SG-cIGw'
# CAR
#GOOGLE_API_KEY = 'AIzaSyBF-dqwU9HViNV9kTbuBzIQCtlbYZz7CV0'

APIS_DB = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'apis.db3'
)


def get_keys():
    """
    Return available keys for this API
    """
    
    from gasp3.dt.fm.sql import query_to_df
    
    keys = query_to_df(APIS_DB, (
        "SELECT fid, key, date, nrqst FROM google "
        "ORDER BY fid"
    ), db_api='sqlite')
    
    return keys


def check_result(result, glg_service):
    if str(result["status"]) == "OK":
        if glg_service == "GEOCODING" or glg_service == "ELEVATION":
            return result["results"]
        
        elif glg_service == "DISTANCE_MATRIX":
            return result["rows"]
    
    elif str(result["status"]) == "ZERO_RESULTS":
        return []
    
    elif str(result['status']) == "OVER_QUERY_LIMIT":
        raise ValueError('Cota diaria foi excedida')
    
    elif str(result['status']) == "REQUEST_DENIED":
        raise ValueError('Access denied')
    
    elif str(result['status']) == 'INVALID_REQUEST':
        raise ValueError('Given query is not valid')
    
    elif str(result['status']) == 'UNKNOWN_ERROR':
        raise ValueError('UNKNOWN ERROR')
    
    elif str(result['status']) == 'MAX_ELEMENTS_EXCEEDED':
        raise ValueError('Numero de elementos excedido')
    
    else:
        return 0


def select_api_key():
    """
    Select the API Key to use
    """
    
    from gasp3.dt.fm.sql import query_to_df
    
    GOOGLE_KEYS_ = query_to_df(
        APIS_DB, "SELECT fid, key, date, nrqst FROM google", db_api='sqlite'
    ).to_dict(orient="records")
    
    GOOGLE_KEYS = [(
        GOOGLE_KEYS_['fid'], GOOGLE_KEYS_['key'], GOOGLE_KEYS_['date'],
        GOOGLE_KEYS_['nrqst']
    ) for k in GOOGLE_KEYS_]
    
    DATE    = datetime.date.today()
    DAYTIME = '{}-{}-{}'.format(
        str(DATE.year),
        str(DATE.month) if len(str(DATE.month)) == 2 else "0" + str(DATE.month),
        str(DATE.day) if len(str(DATE.day)) == 2 else "0" + str(DATE.day)
    )
    
    for k in range(len(GOOGLE_KEYS)):
        if DAYTIME != str(GOOGLE_KEYS[k][2]):
            GOOGLE_API_KEY = GOOGLE_KEYS[k][1]
            API_REQUESTS   = 0
            KEY_FID        = GOOGLE_KEYS[k][0]
        
        else:
            API_REQUESTS = int(GOOGLE_KEYS[k][3])
            if API_REQUESTS >= 2490:
                continue
            
            else:
                GOOGLE_API_KEY = GOOGLE_KEYS[k][1]
                KEY_FID = GOOGLE_KEYS[k][0]
        
        if GOOGLE_API_KEY:
            break
    
    return KEY_FID, GOOGLE_API_KEY, API_REQUESTS


def record_api_utilization(FID_KEY, API_REQUESTS):
    """
    One API Key was used, so record that utilization
    """
    
    from gasp3.sql.mng.tbl import update_query
    
    update_query(
        APIS_DB, "google",
        {"nrqst" : API_REQUESTS, 'date' : "date('now')"},
        {"fid"   : FID_KEY}
    )

