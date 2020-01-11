"""
Overlay operations
"""


"""
Clip Tools
"""

def clip(inFeat, clipFeat, outFeat, api_gis="grass"):
    """
    Clip Analysis
    
    api_gis Options:
    * grass
    * grass_cmd
    * ogr2ogr
    """
    
    if api_gis == "grass":
        from grass.pygrass.modules import Module
        
        vclip = Module(
            "v.clip", input=inFeat, clip=clipFeat,
            output=outFeat, overwrite=True, run_=False, quiet=True
        )
        
        vclip()
    
    elif api_gis == "grass_cmd":
        from gasp import exec_cmd
        
        rcmd = exec_cmd(
            "v.clip input={} clip={} output={} --overwrite --quiet".format(
                inFeat, clipFeat, outFeat
            )
        )
    
    elif api_gis == 'ogr2ogr':
        from gasp            import exec_cmd
        from gasp.pyt.oss    import get_filename
        from gasp.gt.prop.ff import drv_name

        rcmd = exec_cmd((
            "ogr2ogr -f \"{}\" {} {} -clipsrc {} -clipsrclayer {}"
        ).format(
            drv_name(outFeat), outFeat, inFeat, clipFeat,
            get_filename(clipFeat)
        ))
    
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


"""
Intersection in the same Feature Class/Table
"""

def line_intersect_to_pnt(conDB, inShp, outShp):
    """
    Get Points where two line features of the same feature class
    intersects.
    """
    
    from gasp.pyt.oss       import get_filename
    from gasp.gt.to.shp     import dbtbl_to_shp
    from gasp.sql.db        import create_db
    from gasp.sql.to        import shp_to_psql
    from gasp.sql.gop.ovlay import line_intersection_pnt
    
    # Create DB if necessary
    if "DATABASE" not in conDB:
        conDB["DATABASE"] = create_db(conDB, get_filename(
            inShp, forceLower=True
        ))
    
    else:
        from gasp.sql.i import db_exists
        
        isDb = db_exists(conDB, conDB["DATABASE"])
        
        if not isDb:
            conDB["DB"] = conDB["DATABASE"]
            del conDB["DATABASE"]
            conDB["DATABASE"] = create_db(conDB, conDB["DB"])
    
    # Send data to DB
    inTbl = shp_to_psql(conDB, inShp, api="shp2pgsql")
    
    # Get result
    outTbl = line_intersection_pnt(conDB, inTbl, get_filename(
        outShp, forceLower=True))
    
    # Export data from DB
    outShp = dbtbl_to_shp(
        conDB, outTbl, "geom", outShp, inDB='psql',
        tableIsQuery=None, api="pgsql2shp")
    
    return outShp

