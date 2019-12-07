"""
Delete GIS Files
"""

def del_rst(rstname, ascmd=True):
    """
    Delete Raster map of GRASS GIS
    """

    if not ascmd:
        from grass.pygrass.modules import Module

        add = Module(
            "g.remove", type='raster', name=rstname,
            quiet=True, run_=False, flags='f'
        )
        add()
    
    else:
        from gasp import exec_cmd

        rcmd = exec_cmd((
            "g.remove -f type=raster name={} --quiet"
        ).format(rstname))
    
    return 1

