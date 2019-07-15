"""
Spatial Reference Systems Properties
"""

from osgeo import osr

def epsg_to_wkt(epsg):
    s = osr.SpatialReference()
    s.ImportFromEPSG(epsg)
    
    return s.ExportToWkt()


def get_sref_from_epsg(epsg):
    s = osr.SpatialReference()
    s.ImportFromEPSG(epsg)
    
    return s

def get_shp_sref(shp):
    """
    Get Spatial Reference Object from Feature Class/Lyr
    """
    
    from osgeo            import ogr
    from gasp3.gt.prop.ff import drv_name
    
    if type(shp) == ogr.Layer:
        lyr = shp
        
        c = 0
    
    else:
        data = ogr.GetDriverByName(
            drv_name(shp)).Open(shp)
        
        lyr = data.GetLayer()
        c = 1
    
    spref = lyr.GetSpatialRef()
    
    if c:
        del lyr
        data.Destroy()
    
    return spref


def get_gml_epsg(gmlFile):
    """
    Get EPSG of GML File
    """
    
    from xml.dom import minidom
    
    geomTag = [
        'gml:Polygon', 'gml:MultiPolygon', 
        'gml:Point', 'gml:MultiPoint',
        'gml:LineString', 'gml:MultiLineString'
    ]
    
    # Open XML
    xmlDoc = minidom.parse(gmlFile)
    
    epsgValue = None
    for geom in geomTag:
        if epsgValue:
            break
        
        xmlNodes = xmlDoc.getElementsByTagName(geom)
        
        if not xmlNodes:
            continue
        
        epsgValue = xmlNodes[0].attributes["srsName"].value.split(':')[1]
    
    return epsgValue


def get_epsg_shp(shp, returnIsProj=None):
    """
    Return EPSG code of the Spatial Reference System of a Feature Class
    """
    
    from gasp3.pyt.oss import get_fileformat
    
    if get_fileformat(shp) != '.gml':
        proj = get_shp_sref(shp)
    else:
        epsg = get_gml_epsg(shp)
        
        if not epsg:
            raise ValueError(
                '{} file has not Spatial Reference assigned!'.format(shp)
            )
        
        proj = get_sref_from_epsg(int(epsg))
    
    if not proj:
        raise ValueError(
            '{} file has not Spatial Reference assigned!'.format(shp)
        )
    
    epsg = int(str(proj.GetAttrValue(str('AUTHORITY'), 1)))
    
    if not returnIsProj:
        return epsg
    else:
        if proj.IsProjected:
            mod_proj = proj.GetAttrValue(str('projcs'))
            
            if not mod_proj:
                return epsg, None
            else:
                return epsg, True
        
        else:
            return epsg, None


"""
Raster Spatial Reference Systems
"""

def get_epsg_raster(rst, returnIsProj=None):
    """
    Return the EPSG Code of the Spatial Reference System of a Raster
    """
    
    import os
    from osgeo import gdal
    from osgeo import osr
    
    if not os.path.exists(rst):
        raise ValueError(
            "{} does not exist! Please give a valid path to a raster file"
        )
    
    d    = gdal.Open(rst)
    proj = osr.SpatialReference(wkt=d.GetProjection())
    
    if not proj:
        raise ValueError(
            '{} file has not Spatial Reference assigned!'.format(rst)
        )
    
    epsg = int(str(proj.GetAttrValue(str('AUTHORITY'), 1)))
    
    if not returnIsProj:
        return epsg
    else:
        if proj.IsProjected:
            mod_proj = proj.GetAttrValue(str('projcs'))
            
            if not mod_proj:
                return epsg, None
            else:
                return epsg, True
        else:
            return epsg, None

