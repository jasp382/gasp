"""
Tools to give use to the Google Elevation API
"""

from . import select_api_key
from . import record_api_utilization
from . import check_result

from gasp.web import json_fm_httpget
# ------------------------------ #
"""
Global Variables
"""
GOOGLE_ELEVATION_URL = 'https://maps.googleapis.com/maps/api/elevation/json?'
# ------------------------------ #


def pnt_elev(x, y):
    """
    Get point elevation
    """
    
    # Get key
    KEY_FID, GOOGLE_API_KEY, NR_REQUESTS = select_api_key()
    
    # Record KEY utilization
    record_api_utilization(KEY_FID, GOOGLE_API_KEY, NR_REQUESTS + 1)
    
    try:
        elev_array = json_fm_httpget(
            '{url}locations={lat},{lng}&key={key}'.format(
                url=GOOGLE_ELEVATION_URL,
                lat=str(y), lng=str(x), key=GOOGLE_API_KEY
            )
        )
    except:
        raise ValueError(
            'Something went wrong. The URL was {}'.format(URL)
        )
    
    return check_result(elev_array, "ELEVATION")


def pnts_elev(pnt_coords):
    """
    Get Points Elevation
    """
    
    # Get key
    KEY_FID, GOOGLE_API_KEY, NR_REQUESTS = select_api_key()
    
    URL = '{url}locations={loc}&key={key}'.format(
        url=GOOGLE_ELEVATION_URL, key=GOOGLE_API_KEY,
        loc=pnt_coords
    )
    
    record_api_utilization(KEY_FID, NR_REQUESTS + 1)
    
    try:
        elv = json_fm_httpget(URL)
    
    except:
        raise ValueError(
            'Something went wrong. The URL was {}'.format(URL)
        )
    
    return elv


def elevation_to_pntshp(pnt_shp, epsg, fld_name='ELEVATION'):
    """
    Add an elevation attribute to a point feature class
    """
    
    from gasp.fm        import tbl_to_obj
    from gasp.prop.feat import get_gtype
    from gasp.mng.prj   import project
    from gasp.mng.split import split_df
    from gasp.to.obj    import df_to_dict
    from gasp.to.shp    import df_to_shp
    
    # Check Geometries type - shapes should be of type point
    geomt = get_gtype(pnt_shp, name=True, gisApi='ogr')
    if geomt != 'POINT' and geomt != 'MULTIPOINT':
        raise ValueError('All input geometry must be of type point')
    
    src = tbl_to_obj(pnt_shp)
    if epsg != 4326:
        src = project(src, None, 4326, gisApi='pandas')
    
    # Get str with coords
    src["coords"] = src["geometry"].y.astype(str) + "," + \
        src["geometry"].x.astype(str)
    
    # Split dataframe
    dfs = split_df(src, 250)
    
    for df in dfs:
        coord_str = str(df.coords.str.cat(sep="|"))
        
        elvd = pnts_elev(coord_str)
    
    data = elvd
        
    return data
