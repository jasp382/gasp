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

