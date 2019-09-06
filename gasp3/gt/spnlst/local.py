"""
Local Tools
"""

def combine(inRst, outRst, api="pygrass", template=None):
    """
    Combine Rasters
    """
    
    if api == 'pygrass':
        from grass.pygrass.modules import Module
    
        c = Module(
            "r.cross", input=inRst, output=outRst, flags='z',
            overwrite=True, run_=False, quiet=True
        )
    
        c()
    
    elif api == "grass":
        from gasp3 import exec_cmd
        
        rcmd = exec_cmd((
            "r.cross input={} output={} "
            "-z --overwrite --quiet"
        ).format(",".join(inRst), outRst))
    
    elif api == "arcpy":
        import arcpy
        
        if template:
            tempEnvironment0 = arcpy.env.extent
            arcpy.env.extent = template
        
        arcpy.gp.Combine_sa(";".join(inRst), outRst)
        
        if template:
            arcpy.env.extent = tempEnvironment0
    
    else:
        raise ValueError("API {} is not available".format(api))
    
    return outRst


"""
Merge and Combine raster dataset
"""


def rseries(lst, out, meth):
    
    from grass.pygrass.modules import Module
    
    serie = Module(
        'r.series', input=lst, output=out, method=meth,
        overwrite=True, quiet=True, run_=False
    )
    
    serie()
    
    return out

