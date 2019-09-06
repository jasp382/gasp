"""
Feature Classes Properties
"""


def feat_count(shp, gisApi='pandas'):
    """
    Count the number of features in a feature class
    
    API'S Available:
    * gdal;
    * arcpy;
    * pygrass;
    * pandas;
    """
    
    if gisApi == 'ogr':
        from osgeo            import ogr
        from gasp3.gt.prop.ff import drv_name
    
        data = ogr.GetDriverByName(drv_name(shp)).Open(shp, 0)
        lyr = data.GetLayer()
        fcnt = int(lyr.GetFeatureCount())
        data.Destroy()
    
    elif gisApi == 'pygrass':
        from grass.pygrass.vector import VectorTopo
        
        open_shp = VectorTopo(shp)
        open_shp.open(mode='r')
        fcnt = open_shp.num_primitive_of(geom)
    
    elif gisApi == 'pandas':
        from gasp3.dt.fm import tbl_to_obj
        
        gdf = tbl_to_obj(shp)
        
        fcnt = int(gdf.shape[0])
        
        del gdf
    
    else:
        raise ValueError('The api {} is not available'.format(gisApi))
    
    return fcnt


def get_gtype(shp, name=True, py_cls=None, geomCol="geometry",
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


"""
Fields Information
"""

def lst_fld(shp):
    """
    Return a list with every field name in a vectorial layer
    """
    
    from osgeo            import ogr
    from gasp3.gt.prop.ff import drv_name
    
    if type(shp) == ogr.Layer:
        lyr = shp
        c=0
    
    else:
        data = ogr.GetDriverByName(
            drv_name(shp)).Open(shp, 0)
    
        lyr = data.GetLayer()
        c= 1
    
    defn = lyr.GetLayerDefn()
    
    fields = []
    for i in range(0, defn.GetFieldCount()):
        fdefn = defn.GetFieldDefn(i)
        fields.append(fdefn.name)
    
    if c:
        del lyr
        data.Destroy()
    
    return fields


"""
Geometric Properties
"""

def get_cntr_bnd(shp, isFile=None):
    """
    Return centroid (OGR Point object) of a Boundary (layer with a single
    feature).
    """
    
    from osgeo            import ogr
    from gasp3.gt.prop.ff import drv_name
    
    if isFile:
        shp = ogr.GetDriverByName(
            drv_name(shp)).Open(shp, 0)
    
        lyr = shp.GetLayer()
    
        feat = lyr[0]; geom = feat.GetGeometryRef()
    
    else:
        geom = shp
    
    centroid = geom.Centroid()
    
    cnt = ogr.CreateGeometryFromWkt(centroid.ExportToWkt())
    
    shp.Destroy()
    
    return cnt


def area_to_dic(shp):
    """
    Return the following output:
    
    dic = {
        id_feat: area,
        ...,
        id_feat: area
    }
    """
    
    from osgeo            import ogr
    from gasp3.gt.prop.ff import drv_name
    
    o = ogr.GetDriverByName(drv_name(shp)).Open(shp, 0)
    l = o.GetLayer()
    d = {}
    c = 0
    for feat in l:
        g = feat.GetGeometryRef()
        area = g.GetArea()
        d[c] = area
        c += 1
    del l
    o.Destroy()
    return d

