"""
Image Properties
"""

def get_nd(img):
    """
    Return NoData Value
    """

    band = img.GetRasterBand(1)

    return band.GetNoDataValue()


def get_cell_size(img):
    """Return Cellsize"""

    (tlx, x, xr, tly, yr, y) = img.GetGeoTransform()

    return x, y

