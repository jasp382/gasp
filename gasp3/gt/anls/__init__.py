"""
Analysis Tool
"""

def pntDf_to_convex_hull(pntDf, xCol, YCol, epsg, outEpsg=None, outShp=None):
    """
    Create a GeoDataFrame with a Convex Hull Polygon from a DataFrame
    with points in two columns, one with the X Values, other with the Y Values
    """
    
    from scipy.spatial import ConvexHull
    from shapely       import geometry
    from geopandas     import GeoDataFrame
    
    hull = ConvexHull(pntDf[[xCol, YCol]])
    
    poly = geometry.Polygon([[
        pntDf[xCol].iloc[idx], pntDf[yCol].iloc[idx]
    ] for idx in hull.vertices])
    
    convexDf = GeoDataFrame([1], columns=['cat'], crs={
        'init' : 'epsg:' + str(epsg)}, geometry=[poly])
    
    if outEpsg and outEpsg != epsg:
        from gasp3.gt.prj import proj
        
        convexDf = proj(convexDf, None, outEpsg, inEPSG=epsg, gisApi='pandas')
    
    if outShp:
        from gasp3.gt.to.shp import df_to_shp
        
        return df_to_shp(convexDf, outShp)
    
    return convexDf

