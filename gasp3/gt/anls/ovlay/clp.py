"""
Clip Tools
"""

def clip(inFeat, clipFeat, outFeat, api_gis="grass"):
    """
    Clip Analysis
    
    api_gis Options:
    * grass
    * grass_cmd
    """
    
    if api_gis == "grass":
        from grass.pygrass.modules import Module
        
        vclip = Module(
            "v.clip", input=inFeat, clip=clipFeat,
            output=outFeat, overwrite=True, run_=False, quiet=True
        )
        
        vclip()
    
    elif api_gis == "grass_cmd":
        from gasp3 import exec_cmd
        
        rcmd = exec_cmd(
            "v.clip input={} clip={} output={} --overwrite --quiet".format(
                inFeat, clipFeat, outFeat
            )
        )
    
    else:
        raise ValueError("{} is not available!".format(api_gis))
    
    return outFeat


def clip_shp_by_listshp(inShp, clipLst, outLst):
    """
    Clip shapes using as clipFeatures all SHP in clipShp
    Uses a very fast process with a parallel procedures approach
    
    For now, only works with GRASS GIS
    
    Not Working nice with v.clip because of the database
    """
    
    """
    import copy
    from grass.pygrass.modules import Module, ParallelModuleQueue
    
    op_list = []
    
    clipMod = Module(
        "v.clip", input=inShp, overwrite=True, run_=False, quiet=True
    )
    qq = ParallelModuleQueue(nprocs=5)
    
    for i in range(len(clipLst)):
        new_clip = copy.deepcopy(clipMod)
        
        op_list.append(new_clip)
        
        m = new_clip(clip=clipLst[i], output=outLst[i])
        
        qq.put(m)
    qq.wait()
    """
    
    o = [clip(
        inShp, clipLst[i], outLst[i], api_gis="grass_cmd"
    ) for i in range(len(clipLst))]
    
    return outLst
