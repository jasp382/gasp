"""
Data Extraction tools
"""


def geom_by_idx(inShp, idx):
    """
    Get Geometry by index in file
    """
    
    from osgeo            import ogr
    from gasp3.gt.prop.ff import drv_name
    
    src = ogr.GetDriverByName(drv_name(inShp)).Open(inShp)
    lyr = src.GetLayer()
    
    c = 0
    geom = None
    for f in lyr:
        if idx == c:
            geom = f.GetGeometryRef()
        
        else:
            c += 1
    
    if not geom:
        raise ValueError("inShp has not idx")
    
    _geom = geom.ExportToWkt()
    
    del lyr
    src.Destroy()
    
    return _geom