"""
Objects to Geometries
"""

from osgeo import ogr

"""
Create Geometries
"""

def create_point(x, y):
    """
    Return a OGR Point geometry object
    """
    
    pnt = ogr.Geometry(ogr.wkbPoint)
    pnt.AddPoint(float(x), float(y))
    
    return pnt

def create_polygon(points, api='ogr'):
    """
    Return a OGR Polygon geometry object
    """
    
    ring = ogr.Geometry(ogr.wkbLinearRing)
    
    for pnt in points:
        if type(pnt) == tuple or type(pnt) == list:
            ring.AddPoint(pnt[0], pnt[1])
        else:
            ring.AddPoint(pnt.GetX(), pnt.GetY())
    
    polygon = ogr.Geometry(ogr.wkbPolygon)
    polygon.AddGeometry(ring)
    
    return polygon


"""
Play with GeoDataFrames
"""

def pnt_dfwxy_to_geodf(df, colX, colY, epsg):
    """
    Pandas Dataframe with numeric x, y columns
    to GeoDataframe
    
    Works Only for Points
    """
    
    from geopandas        import GeoDataFrame
    from shapely.geometry import Point
    
    geoms = [Point(xy) for xy in zip(df[colX], df[colY])]
    df.drop([colX, colY], axis=1, inplace=True)
    gdata = GeoDataFrame(
        df, crs={'init' : 'epsg:' + str(epsg)},
        geometry=geoms
    )
    
    return gdata


def df_to_geodf(df, colGeom, epsg):
    """
    Regular Pandas Dataframe To GeoDataframe
    """
    
    from geopandas import GeoDataFrame
    
    return GeoDataFrame(
        df, crs={'init' : 'epsg:{}'.format(epsg)},
        geometry=colGeom
    )
