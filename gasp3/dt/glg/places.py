"""
Google Places API Web Service
"""

from . import select_api_key
from . import record_api_utilization

from gasp.web import json_fm_httpget

# ------------------------------ #
"""
Global Variables
"""
GOOGLE_PLACES_URL = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?'
# ------------------------------ #

def get_places_by_radius(lat, lng, radius, keyword=None,
                         _type=None):
    """
    Get Places
    """
    
    def sanitize_coord(coord):
        if ',' in str(coord):
            return str(coord).replace(',', '.')
        
        else:
            return str(coord)
    
    from gasp import unicode_to_str
    
    # Get Google Maps Key
    KEY_FID, GOOGLE_API_KEY, NR_REQUESTS = select_api_key()
    
    # Prepare URL
    keyword = unicode_to_str(keyword) if type(keyword) == unicode else \
        keyword
    
    str_keyword = '' if not keyword else '&keyword={}'.format(
        keyword
    )
    
    _type = unicode_to_str(_type) if type(_type) == unicode else \
        _type
    
    str_type = '' if not _type else '&type={}'.format(_type)
    
    URL = '{url}location={lt},{lg}&radius={r}&key={apik}{kw}{typ}'.format(
        url  = GOOGLE_PLACES_URL,
        apik = GOOGLE_API_KEY,
        lt   = sanitize_coord(lat),
        lg   = sanitize_coord(lng),
        r    = sanitize_coord(radius),
        kw   = str_keyword, typ = str_type
    )
    
    data = json_fm_httpget(URL)
    
    # Record Key utilization
    record_api_utilization(KEY_FID, NR_REQUESTS)
    
    return data


def find_places(inShp, epsg, radius, output, keyword=None, type=None):
    """
    Extract places from Google Maps
    """
    
    import pandas;           import time
    from gasp.fm             import tbl_to_obj
    from gasp.to.geom        import pnt_dfwxy_to_geodf
    from gasp.mng.prj        import project
    from gasp.mng.fld.df     import listval_to_newcols
    from gasp.to.shp         import df_to_shp
    
    pntDf = tbl_to_obj(inShp)
    pntDf = project(pntDf, None, 4326, gisApi='pandas') if epsg != 4326 else pntDf
    
    pntDf['latitude']  = pntDf.geometry.y.astype(str)
    pntDf['longitude'] = pntDf.geometry.x.astype(str)
    
    DATA = 1
    def get_places(row):
        places = get_places_by_radius(
            row.latitude, row.longitude, radius, keyword, type
        )
        
        if type(DATA) == int:
            DATA = pandas.DataFrame(places['results'])
        
        else:
            DATA = DATA.append(
                pandas.DataFrame(places['results']),
                ignore_index=True
            )
    
    a = pntDf.apply(lambda x: get_places(x), axis=1)
    
    DATA = listval_to_newcols(DATA, 'geometry')
    fldsToDelete = ['viewport', 'opening_hours', 'icon', 'plus_code', 'photos']
    realDeletion = [x for x in fldsToDelete if x in DATA.columns.values]
    DATA.drop(realDeletion, axis=1, inplace=True)
    
    DATA = listval_to_newcols(DATA, 'location')
    
    DATA = pnt_dfwxy_to_geodf(DATA, 'lng', 'lat', 4326)
    
    if epsg != 4326:
        DATA = project(DATA, None, epsg, gisApi='pandas')
    
    DATA["types"] = DATA.types.astype(str)
    
    df_to_shp(DATA, output)
    
    return output

