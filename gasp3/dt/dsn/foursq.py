"""
Do things with FourSquare Data
"""

CLIENT_ID     = '4CEA0BIIJKNPKHY3T4XWGEM5QKC5KP2MIO0ODU5RNKICOPPT'
CLIENT_SECRET = 'QVDLNJ01NQ2LCS02AIZSXJI5WZHM5TCH5JRVL1KJUVGOGMCG'


def search_places(lat, lng, radius):
    """
    Search places using an radius as reference.
    """
    
    import pandas
    from gasp3.pyt.web    import data_from_get
    from gasp3.pyt.df.fld import listval_to_newcols
    
    data = data_from_get(
        'https://api.foursquare.com/v2/venues/search', dict(
            client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
            v='20180323', ll='{},{}'.format(str(lat), str(lng)),
            intent='browse', radius=str(radius), limit=50
        )
    )
    
    dataDf = pandas.DataFrame(data['response']['venues'])
    
    if not dataDf.shape[0]: return None
    
    dataDf.drop([
        'contact', 'hasPerk', 'referralId', 'venuePage', 'verified',
        'venueChains', 'id'
    ], axis=1, inplace=True)
    
    dataDf.rename(columns={'name' : 'name_main'}, inplace=True)
    
    dataDf = listval_to_newcols(dataDf, 'location')
    
    dataDf.drop([
        "labeledLatLngs", "neighborhood", "state", "distance",
        "crossStreet", 'country', 'city', 'cc', 'address' 
    ], axis=1, inplace=True)
    
    dataDf["formattedAddress"] = dataDf["formattedAddress"].astype(str)
    
    dataDf = listval_to_newcols(dataDf, 'stats')
    dataDf = listval_to_newcols(dataDf, 'categories')
    dataDf = listval_to_newcols(dataDf, 0)
    
    dataDf.drop([
        "primary", "id", "icon"
    ], axis=1, inplace=True)
    
    dataDf = listval_to_newcols(dataDf, 'beenHere')
    
    dataDf.drop([
        "marked", "unconfirmedCount", "lastCheckinExpiredAt"
    ], axis=1, inplace=True)
    
    return dataDf


def venues_by_query(radialShp, epsgIn, epsgOut=4326, onlySearchAreaContained=True):
    """
    Get absolute location of foursquare data using the Foursquare API and
    Pandas to validate data.
    
    buffer_shp cloud be a shapefile with a single buffer feature
    or a dict like:
    buffer_shp = {
        x: x_value,
        y: y_value,
        r: dist
    }
    
    or a list or a tuple:
    buffer_shp = [x, y, r]
    """
    
    import pandas; from geopandas import GeoDataFrame
    from shapely.geometry         import Polygon, Point
    from gasp3.gt.prop.feat.bf    import getBufferParam
    from gasp3.dt.dsn.foursq      import search_places
    
    x, y, radius = getBufferParam(radialShp, epsgIn, outSRS=4326)
    
    data = search_places(y, x, radius)
    
    try:
        if not data:
            # Return 0
            return 0
    
    except:
        pass
    
    geoms = [Point(xy) for xy in zip(data.lng, data.lat)]
    data.drop(['lng', 'lat'], axis=1, inplace=True)
    gdata = GeoDataFrame(data, crs={'init' : 'epsg:4326'}, geometry=geoms)
    
    if onlySearchAreaContained:
        from shapely.wkt           import loads
        from gasp3.gt.mng.prj      import project_geom
        from gasp3.gt.anls.prox.bf import xy_to_buffer
        
        _x, _y, _radius = getBufferParam(radialShp, epsgIn, outSRS=3857)
        searchArea = xy_to_buffer(float(_x), float(_y), float(_radius))
        searchArea = project_geom(searchArea, 3857, 4326, api='ogr')
        searchArea = loads(searchArea.ExportToWkt())
        
        gdata["tst_geom"] = gdata.geometry.intersects(searchArea)
        gdata = gdata[gdata.tst_geom == True]
        
        gdata.reset_index(drop=True, inplace=True)
        
        gdata.drop('tst_geom', axis=1, inplace=True)
    
    if epsgOut != 4326:
        from gasp3.gt.mng.prj import project
        gdata = project(gdata, None, epsgOut, gisApi='pandas')
    
    return gdata

def venues_to_shp(inShp, inEpsg, outShp, outSRS=4326, onlyInsidePnt=None):
    """
    FourSquare Venues to ESRI Shapefile
    """
    
    from gasp3.dt.to.shp import df_to_shp
    
    df = venues_by_query(
        inShp, inEpsg, epsgOut=outSRS, onlySearchAreaContained=onlyInsidePnt
    )
    
    return df_to_shp(df, outShp)

