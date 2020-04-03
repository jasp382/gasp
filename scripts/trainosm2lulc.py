"""
Produce train from OSM2LULC results
"""

import os
import pandas            as pd
import multiprocessing   as mp
from gasp.gt.sample      import create_fishnet
from gasp.gt.prop.rst    import get_cellsize
from gasp.pyt.oss        import lst_ff, mkdir, fprop, cpu_cores
from gasp.gt.toshp.coord import shpext_to_boundshp
from gasp.gt.wenv.grs    import run_grass
from gasp.gt.torst       import shp_to_rst
from gasp.pyt.df.split   import df_split

def lulc_by_cell(tid, boundary, lulc_shps, fishnet, result, workspace):
    bname = fprop(boundary, 'fn')
    # Boundary to Raster
    ref_rst = shp_to_rst(boundary, None, 10, 0, os.path.join(
        workspace, 'rst_{}.tif'.format(bname)
    ))
    
    # Create GRASS GIS Session
    loc_name = 'loc_' + bname
    gbase = run_grass(workspace, location=loc_name, srs=ref_rst)
    
    import grass.script as grass
    import grass.script.setup as gsetup
    
    gsetup.init(gbase, workspace, loc_name, 'PERMANENT')
    
    # GRASS GIS Modules
    from gasp.gt.toshp.cff import shp_to_grs, grs_to_shp
    from gasp.gt.gop.ovlay import clip, union, intersection
    from gasp.gt.tbl.attr import geomattr_to_db
    
    # Send boundary to GRASS GIS
    b = shp_to_grs(boundary, 'b_' + bname, asCMD=True)
    
    # Send Fishnet to GRASS GIS
    fnet = shp_to_grs(fishnet, fprop(fishnet, 'fn'), asCMD=True)

    # Processing
    ulst = []
    l_lulc_grs = []
    for shp in lulc_shps:
        iname = fprop(shp, 'fn')

        # LULC Class to GRASS GIS
        lulc_grs = shp_to_grs(
            shp, iname + '_large', filterByReg=True, asCMD=True
        )
    
        # Clip LULC Classes using boundary as clip features
        try:
            lulc_grs = clip(lulc_grs, b, iname + '_clip', api_gis="grass")
        except:
            # No areas in fishnet boundary
            # Do nothing
            continue
        
        # Union Fishnet | LULC CLass
        union_grs = union(
            fnet, lulc_grs, iname + '_union', api_gis="grass"
        )
        
        # Get Areas
        geomattr_to_db(union_grs, "areav", "area", "boundary", unit='meters')

        # Export Table
        funion = grs_to_shp(
            union_grs, os.path.join(result, iname + '.shp'), 'area'
        )

        ulst.append(funion)
        l_lulc_grs.append(lulc_grs)
    
    # Intersect between all LULC SHPS
    ist_shp = []
    if len(l_lulc_grs) > 1:
        for i in range(len(l_lulc_grs)):
            for e in range(i+1, len(lulc_grs)):
                try:
                    ist_shp.append(intersection(
                        l_lulc_grs[i], l_lulc_grs[e],
                        'lulcint_' + str(i) + '_' + str(e), api="grass"
                    ))
                except:
                    continue
        
        if len(ist_shp):
            from gasp.gt.gop.genze import dissolve
            from gasp.gt.tbl.grs import reset_table

            if len(ist_shp) > 1:
                from gasp.gt.toshp.mtos import shps_to_shp

                # Export shapes
                _ist_shp = [grs_to_shp(s, os.path.join(
                    workspace, loc_name, s + '.shp'), 'area') for s in ist_shp]
                
                # Merge Intersections
                merge_shp = shps_to_shp(_ist_shp, os.path.join(
                    workspace, loc_name, 'merge_shp.shp'), api='pandas')
                
                # Import GRASS
                merge_shp = shp_to_grs(merge_shp, 'merge_shp')
            
            else:
                merge_shp = ist_shp[0]
            
            # Dissolve Shape
            reset_table(merge_shp, {'refid' : 'varchar(2)'}, {'refid' : '1'})
            overlay_areas = dissolve(merge_shp, 'overlay_areas', 'refid', api='grass')

            # Union Fishnet | Overlay's
            union_ovl = union(fnet, overlay_areas, 'ovl_union', api_gis="grass")

            funion_ovl = grs_to_shp(
                union_ovl, os.path.join(result, union_ovl + '.shp'), 'area'
            )

            ulst.append(funion_ovl)
    
    # Export Tables
    return ulst


def thrd_lulc_by_cell(thrd_id, df_fishnet, l_lulc, result):
    # Create folder for this thread
    t_folder = mkdir(os.path.join(result, 'thrd_' + str(thrd_id)))
    
    # For each fishnet, do the job
    for idx, row in df_fishnet.iterrows():
        rf = mkdir(os.path.join(result, fprop(row.fishnet, 'fn')))

        lulc_by_cell(int(idx), row.bound, l_lulc, row.fishnet, rf, t_folder)


if __name__ == '__main__':
    """
    Parameters
    """

    osmtolulc = '/home/jasp/mrgis/landsense/r_lisboa'
    fishnets  = '/home/jasp/mrgis/landsense/fishnet'
    results   = '/home/jasp/mrgis/landsense/sample_lisboa'

    """
    Run Script
    """
    # List Fishnet
    df_fnet = pd.DataFrame(lst_ff(
        fishnets, file_format='.shp'
    ), columns=['fishnet'])

    # List results
    lst_lulc = lst_ff(osmtolulc, file_format='.shp')

    # Produce boundaries for each fishnet
    bf = mkdir(os.path.join(results, 'boundaries'))

    def produce_bound(row):
        row['bound'] = shpext_to_boundshp(
            row.fishnet, os.path.join(bf, os.path.basename(row.fishnet))
        )

        return row
    
    df_fnet = df_fnet.apply(lambda x: produce_bound(x), axis=1)
    df_fnet['idx'] = df_fnet.index

    n_cpu = cpu_cores()
    dfs = df_split(df_fnet, n_cpu)

    thrds = [mp.Process(
        target=thrd_lulc_by_cell, name='th_{}'.format(str(i+1)),
        args=(i+1, dfs[i], lst_lulc, results)
    ) for i in range(len(dfs))]

    for i in thrds:
        i.start()
    
    for i in thrds:
        i.join()
    
    # Write List of Fishnet
    from gasp.to import obj_to_tbl

    obj_to_tbl(df_fnet, os.path.join(results, 'fishnet_list.xlsx'))

