"""
To tools
"""


def fext_to_geof(inF, outF, ocellsize=10):
    """
    Extent of a File to Raster or Shapefile
    """
    
    from gasp.gt.prop.ext import get_ext
    from gasp.gt.prop.ff  import check_isRaster
    from gasp.gt.prop.prj import get_epsg
    
    # Get extent
    left, right, bottom, top = get_ext(inF)
    
    # Get EPSG of inF
    EPSG = get_epsg(inF)
    
    # Export Boundary
    isRst = check_isRaster(outF)
    
    if isRst:
        from gasp.gt.torst import ext_to_rst
        
        return ext_to_rst(
            (left, top), (right, bottom), outF,
            cellsize=ocellsize, epsg=EPSG, invalidResultAsNull=None
        )
    else:
        from gasp.gt.prop.ff import check_isShp
        
        isShp = check_isShp(outF)
        
        if isShp:
            from gasp.gt.toshp.coord import coords_to_boundshp
            
            return coords_to_boundshp(
                (left, top), (right, bottom), EPSG, outF
            )
        
        else:
            raise ValueError(
                '{} is not recognized as a file with GeoData'.format(
                    inF
                )
            )
