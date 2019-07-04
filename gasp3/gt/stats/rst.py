"""
Statistics using tables
"""

import numpy
from osgeo import gdal


def frequencies(r):
    """
    Return frequencies table
    """
    
    from gasp.fm.rst        import rst_to_array
    from gasp.prop.rst import get_nodata
    from gasp.num           import count_where
    
    if type(r) == str:
        img = rst_to_array(r)
    else:
        img = r
    
    unique = list(numpy.unique(img))
    
    nodataVal = get_nodata(r, gisApi='gdal') if type(r) == str else None
    if nodataVal in unique:
        unique.remove(nodataVal)
    
    return { v : count_where(img, img==v) for v in unique }


def get_percentage_value(rst, value, includeNodata=None):
    """
    Return the % of cells with a certain value
    """
    
    from gasp.num      import count_where
    from gasp.fm.rst   import rst_to_array
    from gasp.prop.rst import get_nodata
    
    array = rst_to_array(rst)
    
    lnh, col = array.shape
    nrcell = lnh * col
    
    if not includeNodata:
        nd = get_nodata(rst, gisApi='gdal')
        
        nd_cells = count_where(array, array == nd)
        
        nrcell = nrcell - nd_cells
    
    valCount = count_where(array, array == value)
    
    perc = (valCount / float(nrcell)) * 100
    
    return perc


def percentage_nodata(rst):
    """
    Return the % of cells with nodata value
    """
    
    from gasp.num      import count_where
    from gasp.fm.rst   import rst_to_array
    from gasp.prop.rst import get_nodata
    
    array = rst_to_array(rst)
    
    lnh, col = array.shape
    nrcell = lnh * col
    
    nd = get_nodata(rst, gisApi='gdal')
    nd_cells = count_where(array, array == nd)
    
    perc = (nd_cells / float(nrcell)) * 100
    
    return perc

