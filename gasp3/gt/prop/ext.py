"""
Extent related
"""


def get_ext(inFile):
    """
    Get Extent of any GIS Data
    
    return None if inFile is not a GIS File
    """
    
    from gasp3.gt.prop.ff import check_isRaster, check_isShp
    
    if check_isRaster(inFile):
        from gasp3.gt.prop.rst import rst_ext
        
        return rst_ext(inFile)
    
    else:
        if check_isShp(inFile):
            from gasp3.gt.prop.feat import get_ext as gext
            
            return gext(inFile)
        
        else:
            return None

