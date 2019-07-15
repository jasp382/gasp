"""
Feature Classes Properties
"""


def get_geom_type(shp, name=True, py_cls=None, geomCol="geometry",
                  gisApi='pandas'):
    """
    Return the Geometry Type of one Feature Class or GeoDataFrame
    
    API'S Available:
    * ogr;
    * pandas;
    """
    
    if gisApi == 'pandas':
        from pandas import DataFrame
        
        if not isinstance(shp, DataFrame):
            from gasp3.dt.fm import tbl_to_obj
            
            gdf     = tbl_to_obj(shp)
            geomCol = "geometry"
        
        else:
            gdf = shp
        
        g = gdf[geomCol].geom_type.unique()
        
        if len(g) == 1:
            return g[0]
        
        elif len(g) == 0:
            raise ValueError(
                "It was not possible to identify geometry type"
            )
        
        else:
            for i in g:
                if i.startswith('Multi'):
                    return i
    
    elif gisApi == 'ogr':
        from osgeo            import ogr
        from gasp3.gt.prop.ff import drv_name
        
        def geom_types():
            return {
                "POINT"           : ogr.wkbPoint,
                "MULTIPOINT"      : ogr.wkbMultiPoint,
                "LINESTRING"      : ogr.wkbLineString,
                "MULTILINESTRING" : ogr.wkbMultiLineString,
                "POLYGON"         : ogr.wkbPolygon,
                "MULTIPOLYGON"    : ogr.wkbMultiPolygon
            }
        
        d = ogr.GetDriverByName(drv_name(shp)).Open(shp, 0)
        l = d.GetLayer()
        
        geomTypes = []
        for f in l:
            g = f.GetGeometryRef()
            n = str(g.GetGeometryName())
            
            if n not in geomTypes:
                geomTypes.append(n)
        
        if len(geomTypes) == 1:
            n = geomTypes[0]
        
        elif len(geomTypes) == 2:
            for i in range(len(geomTypes)):
                if geomTypes[i].startswith('MULTI'):
                    n = geomTypes[i]
        
        else:
            n = None
        
        d.Destroy()
        del l
        
        return {n: geom_types()[n]} if name and py_cls else n \
                if name and not py_cls else geom_types()[n] \
                if not name and py_cls else None
    
    else:
        raise ValueError('The api {} is not available'.format(gisApi))


"""
Extent of Shapefiles and such
"""

def get_ext(shp):
    """
    Return extent of a Vectorial file
    
    Return a tuple object with the follow order:
    (left, right, bottom, top)
    
    API'S Available:
    * ogr;
    """
    
    gisApi = 'ogr'
    
    if gisApi == 'ogr':
        from osgeo            import ogr
        from gasp3.gt.prop.ff import drv_name
    
        dt = ogr.GetDriverByName(drv_name(shp)).Open(shp, 0)
        lyr = dt.GetLayer()
        extent = lyr.GetExtent()
    
        dt.Destroy()
    
    return list(extent)

