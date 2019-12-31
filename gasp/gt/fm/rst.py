"""
Raster to array
"""

import numpy

def rst_to_array(r, flatten=False, with_nodata=True):
    """
    Convert Raster image to numpy array
    
    If flatten equal a True, the output will have a shape of (1, 1).
    
    If with_nodata equal a True, the output will have the nodata values
    """
    
    from osgeo import gdal
    
    img = gdal.Open(r)
    arr = numpy.array(img.ReadAsArray())
    
    if flatten==False and with_nodata==True:
        return arr
    
    elif flatten==True and with_nodata==True:
        return arr.flatten()
    
    elif flatten==True and with_nodata==False:
        band = img.GetRasterBand(1)
        no_value = band.GetNoDataValue()
        values = arr.flatten()
        clean_values = numpy.delete(
            values, numpy.where(values==no_value), None)
        return clean_values

