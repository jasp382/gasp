"""
To tools
"""


def fext_to_geof(inF, outF):
    """
    Extent of a File to Raster or Shapefile
    """
    
    from gasp3.gt.prop.ext import get_ext
    from gasp3.gt.prop.ff  import check_isRaster
    from gasp3.gt.prop.prj import get_epsg
    
    # Get extent
    left, right, bottom, top = get_ext(inF)
    
    # Get EPSG of inF
    EPSG = get_epsg(inF)
    
    # Export Boundary
    isRst = check_isRaster(outF)
    
    if isRst:
        from gasp3.gt.to.rst import ext_to_rst
        
        return ext_to_rst(
            (left, top), (right, bottom), outF,
            cellsize=10, epsg=EPSG, invalidResultAsNull=None
        )
    else:
        from gasp3.gt.prop.ff import check_isShp
        
        isShp = check_isShp(outF)
        
        if isShp:
            from gasp3.gt.to.shp import coords_to_boundary
            
            return coords_to_boundary(
                (left, top), (right, bottom), EPSG, outF
            )
        
        else:
            raise ValueError(
                '{} is not recognized as a file with GeoData'.format(
                    inF
                )
            )
