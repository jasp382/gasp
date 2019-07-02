"""
Data to Rasster File
"""

def rst_to_grs(rst, grsRst, as_cmd=None):
    """
    Raster to GRASS GIS Raster
    """
    
    if not as_cmd:
        from grass.pygrass.modules import Module
        
        m = Module(
            "r.in.gdal", input=rst, output=grsRst, flags='o',
            overwrite=True, run_=False, quiet=True
        )
        
        m()
    
    else:
        from gasp3 import exec_cmd
        
        rcmd = exec_cmd((
            "r.in.gdal input={} output={} -o --overwrite "
            "--quiet"
        ).format(rst, grsRst))
    
    return grsRst


def grs_to_rst(grsRst, rst, as_cmd=None, allBands=None):
    """
    GRASS Raster to Raster
    """
    
    from gasp3.gt.prop.ff import grs_rst_drv
    from gasp3.pyt.oss    import get_fileformat
    
    rstDrv = grs_rst_drv()
    rstExt = get_fileformat(rst)
    
    if not as_cmd:
        from grass.pygrass.modules import Module
        
        m = Module(
            "r.out.gdal", input=grsRst, output=rst,
            format=rstDrv[rstExt], flags='c' if not allBands else '',
            createopt="INTERLEAVE=PIXEL,TFW=YES" if allBands else '',
            overwrite=True, run_=False, quiet=True
        )
        
        m()
    
    else:
        from gasp3 import exec_cmd
        
        rcmd = exec_cmd((
            "r.out.gdal input={} output={} format={} "
            "{} --overwrite --quiet"
        ).format(
            grsRst, rst, rstDrv[rstExt],
            "-c" if not allBands else "createopt=\"INTERLEAVE=PIXEL,TFW=YES\""
        ))
    
    return rst

