"""
Topological Tools
"""

"""
Object Based
"""

def point_in_polygon(point, polygon):
    """
    Point is Inside Polygon?
    """
    
    return point.Within(polygon)


"""
File Based
"""


def orig_dest_to_polyline(srcPoints, srcField, 
                          destPoints, destField, outShp):
    """
    Connect origins to destinations with a polyline which
    length is the minimum distance between the origin related
    with a specific destination.
    
    One origin should be related with one destination.
    These relations should be expressed in srcField and destField
    """
    
    from geopandas        import GeoDataFrame
    from shapely.geometry import LineString
    from gasp.fm          import tbl_to_obj
    from gasp.gt.to.shp   import df_to_shp
    
    srcPnt = tbl_to_obj(srcPoints)
    desPnt = tbl_to_obj(destPoints)
    
    joinDf = srcPnt.merge(destPnt, how='inner',
                          left_on=srcField, right_on=destField)
    
    joinDf["geometry"] = joinDf.apply(
        lambda x: LineString(
            x["geometry_x"], x["geometry_y"]
        ), axis=1
    )
    
    joinDf.drop(["geometry_x", "geometry_y"], axis=1, inplace=True)
    
    a = GeoDataFrame(joinDf)
    
    df_to_shp(joinDf, outShp)
    
    return outShp

