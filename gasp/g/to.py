"""
Something to Geom
"""

def coords_to_boundary(topLeft, lowerRight, epsg, outEpsg=None):
    """
    Top Left and Lower Right to Boundary
    """

    from osgeo import ogr
    from gasp.gt.to.geom import create_polygon

    boundary_points = [
        (   topLeft[0],    topLeft[1]),
        (lowerRight[0],    topLeft[1]),
        (lowerRight[0], lowerRight[1]),
        (   topLeft[0], lowerRight[1]),
        (   topLeft[0],    topLeft[1])
    ]

    # Create polygon
    polygon = create_polygon(boundary_points)

    # Convert SRS if outEPSG
    if outEpsg and epsg != outEpsg:
        from gasp.gt.prj import proj

        poly = proj(polygon, None, outEpsg, inEPSG=epsg, gisApi='OGRGeom')

        return poly
    else:
        return polygon


def shpext_to_boundary(in_shp):
    """
    Read one feature class extent and create a boundary with that
    extent
    """

    from gasp.gt.prop.ext import get_ext
    from gasp.gt.to.geom  import create_polygon

    # Get Extent
    ext = get_ext(in_shp)

    # Create points of the new boundary based on the extent
    boundary_points = [
        (ext[0], ext[3]), (ext[1], ext[3]),
        (ext[1], ext[2]), (ext[0], ext[2]), (ext[0], ext[3])
    ]
    polygon = create_polygon(boundary_points)

    return polygon

