"""
Data analysis By Overlay Tools
"""

def union(lyrA, lyrB, outShp, api_gis="grass_cmd"):
    """
    Calculates the geometric union of the overlayed polygon layers, i.e.
    the intersection plus the symmetrical difference of layers A and B.
    
    API's Available:
    * saga;
    * grass_cmd;
    * grass_cmd;
    """
    
    if api_gis == "saga":
        from gasp import exec_cmd
        
        rcmd = exec_cmd((
            "saga_cmd shapes_polygons 17 -A {} -B {} -RESULT {} -SPLIT 1"
        ).format(lyrA, lyrB, outShp))
    
    elif api_gis == "grass":
        from grass.pygrass.modules import Module
        
        un = Module(
            "v.overlay", ainput=lyrA, atype="area",
            binput=lyrB, btype="area", operator="or",
            output=outShp, overwrite=True, run_=False, quiet=True
        )
        
        un()
    
    elif api_gis == "grass_cmd":
        from gasp import exec_cmd
        
        outcmd = exec_cmd((
            "v.overlay ainput={} atype=area binput={} btype=area "
            "operator=or output={} --overwrite --quiet"
        ).format(lyrA, lyrB, outShp))
    
    else:
        raise ValueError("{} is not available!".format(api_gis))
    
    return outShp


def union_for_all_pairs(inputList):
    """
    Calculates the geometric union of the overlayed polygon layers 
    for all pairs in inputList
    
    THis is not a good idea! It is only an example!
    """
    
    import copy
    from grass.pygrass.modules import Module, ParallelModuleQueue
    
    op_list = []
    
    unionTool = Module(
        "v.overlay", atype="area", btype="area", operator="or",
        overwrite=True, run_=False, quiet=True
    )
    
    qq = ParallelModuleQueue(nprocs=5)
    outputs = []
    for lyr_a, lyr_b in inputList:
        new_union = copy.deepcopy(unionTool)
        op_list.append(new_union)
        
        un_result = "{}_{}".format(lyr_a, lyr_b)
        nu = new_union(
            ainput=lyr_a, binput=lyr_b, ouput=un_result
        )
        
        qq.put(nu)
        outputs.append(un_result)
    
    qq.wait()
    
    return outputs


def optimized_union_anls(lyr_a, lyr_b, outShp, ref_boundary, epsg,
                         workspace=None, multiProcess=None):
    """
    Optimized Union Analysis
    
    Goal: optimize v.overlay performance for Union operations
    """
    
    import os
    from gasp3.pyt.oss       import get_filename
    from gasp3.gt.mng.sample import create_fishnet
    from gasp3.gt.wenv.grs   import run_grass
    from gasp3.gt.mng.feat   import eachfeat_to_newshp
    from gasp3.gt.mng.gen    import merge_feat
    from gasp3.gt.anls.exct  import split_shp_by_attr
    
    if workspace:
        if not os.path.exists(workspace):
            from gasp3.pyt.oss import create_folder
            
            create_folder(workspace, overwrite=True)
    
    else:
        from gasp3.pyt.oss import create_folder
        
        workspace = create_folder(os.path.join(
            os.path.dirname(outShp), "union_work"))
    
    # Create Fishnet
    gridShp = create_fishnet(
        ref_boundary, os.path.join(workspace, 'ref_grid.shp'),
        rowN=4, colN=4
    )
    
    # Split Fishnet in several files
    cellsShp = eachfeat_to_newshp(gridShp, workspace, epsg=epsg)
    
    if not multiProcess:
        # INIT GRASS GIS Session
        grsbase = run_grass(workspace, location="grs_loc", srs=ref_boundary)
        
        import grass.script.setup as gsetup
        
        gsetup.init(grsbase, workspace, "grs_loc", 'PERMANENT')
        
        # Add data to GRASS GIS
        from gasp3.gt.to.shp import shp_to_grs
        
        cellsShp   = [shp_to_grs(
            shp, get_filename(shp), asCMD=True
        ) for shp in cellsShp]
        
        LYR_A = shp_to_grs(lyr_a, get_filename(lyr_a), asCMD=True)
        LYR_B = shp_to_grs(lyr_b, get_filename(lyr_b), asCMD=True)
        
        # Clip Layers A and B for each CELL in fishnet
        LYRS_A = [clip(
            LYR_A, cellsShp[x], LYR_A + "_" + str(x), api_gis="grass_cmd"
        ) for x in range(len(cellsShp))]; LYRS_B = [clip(
            LYR_B, cellsShp[x], LYR_B + "_" + str(x), api_gis="grass_cmd"
        ) for x in range(len(cellsShp))]
        
        # Union SHPS
        UNION_SHP = [union(
            LYRS_A[i], LYRS_B[i], "un_{}".format(i), api_gis="grass_cmd"
        ) for i in range(len(cellsShp))]
        
        # Export Data
        from gasp3.gt.to.shp import grs_to_shp
        
        _UNION_SHP = [grs_to_shp(
            shp, os.path.join(workspace, shp + ".shp"), "area"
        ) for shp in UNION_SHP]
    
    else:
        def clip_and_union(la, lb, cell, work, ref, proc, output):
            # Start GRASS GIS Session
            grsbase = run_grass(work, location="proc_" + str(proc), srs=ref)
            import grass.script.setup as gsetup
            gsetup.init(grsbase, work, "proc_" + str(proc), 'PERMANENT')
            
            # Import GRASS GIS modules
            from gasp3.gt.to.shp import shp_to_grs
            from gasp3.gt.to.shp import grs_to_shp
            
            # Add data to GRASS
            a = shp_to_grs(la, get_filename(la), asCMD=True)
            b = shp_to_grs(lb, get_filename(lb), asCMD=True)
            c = shp_to_grs(cell, get_filename(cell), asCMD=True)
            
            # Clip
            a_clip = clip(a, c, "{}_clip".format(a), api_gis="grass_cmd")
            b_clip = clip(b, c, "{}_clip".format(b), api_gis="grass_cmd")
            
            # Union
            u_shp = union(a_clip, b_clip, "un_{}".format(c), api_gis="grass_cmd")
            
            # Export
            o = grs_to_shp(u_shp, output, "area")
        
        import multiprocessing
        
        thrds = [multiprocessing.Process(
            target=clip_and_union, name="th-{}".format(i), args=(
                lyr_a, lyr_b, cellsShp[i],
                os.path.join(workspace, "th_{}".format(i)), ref_boundary, i,
                os.path.join(workspace, "uniao_{}.shp".format(i))
            )
        ) for i in range(len(cellsShp))]
        
        for t in thrds:
            t.start()
        
        for t in thrds:
            t.join()
        
        _UNION_SHP = [os.path.join(
            workspace, "uniao_{}.shp".format(i)
        ) for i in range(len(cellsShp))]
    
    # Merge all union into the same layer
    MERGED_SHP = merge_feat(_UNION_SHP, outShp, api="ogr2ogr")
    
    return outShp


def intersection(inShp, intersectShp, outShp, api='geopandas'):
    """
    Intersection between ESRI Shapefile
    
    'API's Available:
    * geopandas
    * saga;
    * pygrass
    """
    
    if api == 'geopandas':
        import geopandas
    
        from gasp3.fm        import tbl_to_obj
        from gasp3.gt.to.shp import df_to_shp
    
        dfShp       = tbl_to_obj(inShp)
        dfIntersect = tbl_to_obj(intersectShp)
    
        res_interse = geopandas.overlay(dfShp, dfIntersect, how='intersection')
    
        df_to_shp(res_interse, outShp)
    
    elif api == 'saga':
        from gasp3 import exec_cmd
        
        cmdout = exec_cmd((
            "saga_cmd shapes_polygons 14 -A {} -B {} -RESULT {} -SPLIT 1"
        ).format(inShp, intersectShp, outShp))
    
    elif api == 'pygrass':
        from grass.pygrass.modules import Module
        
        clip = Module(
            "v.overlay", ainput=inShp, atype="area",
            binput=intersectShp, btype="area", operator="and",
            output=outShp,  overwrite=True, run_=False, quiet=True
        )
        
        clip()
        
    else:
        raise ValueError("{} is not available!".format(api))
    
    return outShp


def self_intersection(polygons, output):
    """
    Create a result with the self intersections
    """
    
    from gasp3 import exec_cmd
    
    cmd = (
        'saga_cmd shapes_polygons 12 -POLYGONS {in_poly} -INTERSECT '
        '{out}'
    ).format(in_poly=polygons, out=output)
    
    outcmd = exec_cmd(cmd)
    
    return output


def erase(inShp, erase_feat, out, splitMultiPart=None, notTbl=None,
          api='pygrass'):
    """
    Difference between two feature classes
    
    API's Available:
    * pygrass;
    * grass;
    * saga;
    """
    
    if api == 'saga':
        """
        Using SAGA GIS
        
        It appears to be very slow
        """
        from gasp3 import exec_cmd
    
        cmd = (
            'saga_cmd shapes_polygons 15 -A {in_shp} -B {erase_shp} '
            '-RESULT {output} -SPLIT {sp}'
        ).format(
            in_shp=inShp, erase_shp=erase_feat,
            output=out,
            sp='0' if not splitMultiPart else '1'
        )
    
        outcmd = exec_cmd(cmd)
    
    elif api == 'pygrass':
        """
        Use pygrass
        """
        
        from grass.pygrass.modules import Module
        
        erase = Module(
            "v.overlay", ainput=inShp, atype="area",
            binput=erase_feat, btype="area", operator="not",
            output=out, overwrite=True, run_=False, quiet=True,
            flags='t' if notTbl else None
        )
    
        erase()
    
    elif api == 'grass':
        """
        Use GRASS GIS tool via command line
        """
        
        from gasp3 import exec_cmd
        
        rcmd = exec_cmd((
            "v.overlay ainput={} atype=area binput={} "
            "btype=area operator=not output={} {}"
            "--overwrite --quiet"
        ).format(inShp, erase_feat, out, "" if not notTbl else "-t "))
    
    else:
        raise ValueError('API {} is not available!'.format(api))
    
    return out
