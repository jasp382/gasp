"""
Image Properties
"""

def get_nd(img):
    """
    Return NoData Value
    """

    band = img.GetRasterBand(1)

    return band.GetNoDataValue()

