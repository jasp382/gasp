"""
GRASS Fields
"""

def add_field(shp, fld, fld_type, lyrN=1, ascmd=None):
    """
    fld_type options:
    * VARCHAR()
    * INT
    * DOUBLE PRECISION
    * DATE
    """
    
    if not ascmd:
        from grass.pygrass.modules import Module
        
        c = Module(
            "v.db.addcolumn", map=shp, layer=lyrN,
            columns='{} {}'.format(fld, fld_type),
            run_=False, quiet=True
        )
    
        c()
    
    else:
        from gasp import exec_cmd
        
        rcmd = exec_cmd((
            "v.db.addcolumn map={} layer={} columns=\"{} {}\" --quiet"
        ).format(shp, lyrN, fld, fld_type))


def rename_col(tbl, oldCol, newCol, as_cmd=None):
    """
    Renames a column in the attribute table connected to a given vector map.
    """
    
    if not as_cmd:
        from grass.pygrass.modules import Module
        
        func = Module(
            "v.db.renamecolumn", map=tbl, column="{},{}".format(oldCol, newCol),
            quiet=True, run_=False
        )
        
        func()
    else:
        from gasp3 import exec_cmd
        
        rcmd = exec_cmd(
            "v.db.renamecolumn map={} layer=1 column={},{}".format(
                tbl, oldCol, newCol
            )
        )
