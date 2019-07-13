"""
Something to Feature Class
"""

def df_to_shp(indf, outShp):
    """
    Pandas Dataframe to ESRI Shapefile
    """
    
    import geopandas
    
    indf.to_file(outShp)
    
    return outShp


def coords_to_boundary(topLeft, lowerRight, epsg, outshp,
                       outEpsg=None):
    """
    Top Left and Lower Right to Boundary
    """
    
    import os
    from osgeo             import ogr
    from gasp3.gt.prop.ff  import drv_name
    from gasp3.gt.prop.prj import get_sref_from_epsg
    from gasp3.pyt.oss     import get_filename
    
    boundary_points = [
        (   topLeft[0],    topLeft[1]),
        (lowerRight[0],    topLeft[1]),
        (lowerRight[0], lowerRight[1]),
        (   topLeft[0], lowerRight[1]),
        (   topLeft[0],    topLeft[1])
    ]
    
    # Convert SRS if outEPSG
    if outEpsg and epsg != outEpsg:
        from gasp3.to.geom    import create_polygon
        from gasp3.gt.mng.prj import project_geom
        
        poly = project_geom(
            create_polygon(boundary_points), epsg, outEpsg)
        
        left, right, bottom, top = poly.GetEnvelope()
        
        boundary_points = [
            (left, top), (right, top), (right, bottom),
            (left, bottom), (left, top)
        ]
    
    shp = ogr.GetDriverByName(
        drv_name(outshp)).CreateDataSource(outshp)
    
    SRS_OBJ = get_sref_from_epsg(epsg) if not outEpsg else \
        get_sref_from_epsg(outEpsg)
    lyr = shp.CreateLayer(
        get_filename(outshp), SRS_OBJ, geom_type=ogr.wkbPolygon
    )
    
    outDefn = lyr.GetLayerDefn()
    
    feat = ogr.Feature(outDefn)
    ring = ogr.Geometry(ogr.wkbLinearRing)
    
    for pnt in boundary_points:
        ring.AddPoint(pnt[0], pnt[1])
    
    polygon = ogr.Geometry(ogr.wkbPolygon)
    polygon.AddGeometry(ring)
    
    feat.SetGeometry(polygon)
    lyr.CreateFeature(feat)
    
    feat.Destroy()
    shp.Destroy()
    
    return outshp

