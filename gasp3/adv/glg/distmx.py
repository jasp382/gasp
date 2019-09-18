"""
Operations with the Google Maps Distance Matrix API
"""


from gasp3.pyt.web import http_to_json

from . import select_api_key
from . import record_api_utilization
from . import check_result

# ------------------------------ #
"""
Global Variables
"""
GOOGLE_DISTMATRIX_URL = 'https://maps.googleapis.com/maps/api/distancematrix/json?'
# ------------------------------ #


def dist_matrix(origins, destination, NORIGINS, NDEST,
                transport_mode=None, useKey=None):
    """
    Get distance matrix considering several origins and destinations
    
    Avaiable transport modes:
    * driving (standard) - indica que a distancia deve ser calculada usando a
    rede de estradas.
    
    * walking - solicita o calculo de distancia para caminhadas por vias
    para pedestres e calcadas (quando disponiveis).
    
    * bicycling - solicita o calculo de distancia para bicicleta por
    ciclovias e ruas preferencias (quando disponiveis).
    
    * transit - solicita o calculo de distancia por rotas de transporte
    publico (quando disponiveis). O valor so podera ser especificado se a
    solicitacao incluir uma chave de API ou um ID de cliente do Google Maps
    APIs Premium Plan. Se voce definir o modo como transit, podera especificar
    um valor de departure_time ou arrival_time. Se nenhum desses valores
    for especificado, o valor padrao de departure_time sera "now" (ou seja,
    o horario de partida padrao e o atual). Ha tambem a opcao para
    incluir um transit_mode e/ou uma transit_routing_preference.
    """
    
    def sanitize_coords(pair):
        if type(pair) == tuple:
            x, y = str(pair[0]), str(pair[1])
        
            return '{},{}'.format(
                y if ',' not in y else y.replace(',', '.'),
                x if ',' not in x else x.replace(',', '.')
            )
        
        elif type(pair) == str:
            return pair
        
        else:
            raise ValueError("Values of origins/destinations are not valid")
    
    origins_str = str(origins) if type(origins) == str else \
        '|'.join([sanitize_coords(x) for x in origins]) \
        if type(origins) == list else None
    
    destination_str = str(destination) if type(destination) == str else \
        '|'.join([sanitize_coords(x) for x in destination]) \
        if type(destination) == list else None
    
    if not origins_str or not destination_str:
        raise ValueError(
            'origins or destination value is not valid'
        )
    
    if useKey:
        KEY_FID, GOOGLE_API_KEY, NR_REQUESTS = None, useKey, None
    else:
        # Get Key to be used
        KEY_FID, GOOGLE_API_KEY, NR_REQUESTS = select_api_key()
    
    transport_mode = 'driving' if not transport_mode else transport_mode
    
    URL = (
        '{u}origins={o_str}&destinations={d_str}&'
        'mode={m}&key={api_key}'
    ).format(
        u       = GOOGLE_DISTMATRIX_URL, o_str = origins_str,
        d_str   = destination_str      , m     = transport_mode,
        api_key = GOOGLE_API_KEY
    )
    
    # Record api utilization
    if not useKey:
        record_api_utilization(KEY_FID, NR_REQUESTS + NORIGINS + NDEST)
    
    try:
        matrix = http_to_json(URL)
    except:
        raise ValueError(
            'Something went wrong. The URL was {}'.format(URL)
        )
    
    return check_result(matrix, "DISTANCE_MATRIX")


def get_max_dist(pntA, pntB):
    """
    Receive two Arrays - pntA & pntB - and calculate distance between
    each possible pair.
    
    Return the maximum distance
    """
    
    def pnt_to_str(l):
        return '|'.join([
            '{lat},{lng}'.format(
                lat=str(pnt[1]).replace(',', '.'),
                lng=str(pnt[0]).replace(',', '.')
            ) for pnt in l
        ])
    
    # pntA to String
    pntA_str = pnt_to_str(pntA)
    
    # pntB to String
    pntB_str = pnt_to_str(pntB)
    
    # Get matrix distance
    matrix = get_distance_matrix(pntA_str, pntB_str)
    
    # Get maximum
    MAX_DISTANCE = 0
    for row in matrix['rows']:
        for col in row['elements']:
            distance = col['duration']['value'] / 60.0
            
            if not MAX_DISTANCE:
                MAX_DISTANCE = distance
            else:
                if distance > MAX_DISTANCE:
                    MAX_DISTANCE = distance
                else:
                    continue
    
    return MAX_DISTANCE
