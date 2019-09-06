"""
Network and Raster
"""


def cost_surface(dem, lulc, cls_lulc, prod_lulc, roads, kph, barr,
                    grass_location, output, grass_path=None):
    """
    Tool for make a cost surface based on the roads, slope, land use and
    physical barriers. ach cell has a value that represents the resistance to
    the movement.
    """
    
    import os
    from gasp3.pyt.oss     import os_name, create_folder
    from gasp3.gt.wenv.grs import run_grass
    from gasp3.gt.prop.rst import get_cellsize, rst_distinct
    from .constants        import lulc_weight
    from .constants        import get_slope_categories
    
    """
    Auxiliar Methods
    """
    def edit_lulc(shp, fld_cls, new_cls):
        FT_TF_GRASS(shp, 'lulc', 'None')
        add_field('lulc', 'leg', 'INT')
        for key in new_cls.keys():
            l = new_cls[key]['cls']
            sql = " OR ".join(["{campo}='{value}'".format(campo=fld_cls, value=i) for i in l])
            update_table('lulc', 'leg', int(key), sql)
        return {'shp':'lulc', 'fld':'leg'}
    
    def combine_to_cost(rst_combined, lst_rst, work, slope_weight,
                        rdv_cos_weight, cellsize, mode_movement):
        # The tool r.report doesn't work properly, for that we need some aditional information
        l = []
        for i in lst_rst:
            FT_TF_GRASS(i, os.path.join(work, i + '.tif'), 'None')
            values = rst_distinct(os.path.join(work, i + '.tif'), gisApi='gdal')
            l.append(min(values))
        # ******
        # Now, we can procede normaly
        txt_file = os.path.join(work, 'text_combine.txt')
        raster_report(rst_combined, txt_file)
        open_txt = open(txt_file, 'r')
        c = 0
        dic_combine = {}
        for line in open_txt.readlines():
            try:
                if c == 4:
                    dic_combine[0] = [str(l[0]), str(l[1])]
                elif c >= 5:
                    pl = line.split('|')
                    cat = pl[2].split('; ')
                    cat1 = cat[0].split(' ')
                    cat2 = cat[1].split(' ')
                    dic_combine[int(pl[1])] = [cat1[1], cat2[1]]
                c += 1
            except:
                break
        
        cst_dic = {}
        for key in dic_combine.keys():
            cls_slope = int(dic_combine[key][0])
            cos_vias = int(dic_combine[key][1])
            if cos_vias >= 6:
                weight4slope = slope_weight[cls_slope]['rdv']
                if mode_movement == 'pedestrian':
                    weight4other = (3600.0 * cellsize) / (5.0 * 1000.0)
                else:
                    weight4other = (3600.0 * cellsize) / (cos_vias * 1000.0)
            else:
                weight4slope = slope_weight[cls_slope]['cos']
                weight4other = rdv_cos_weight[cos_vias]['weight']
            cst_dic[key] = (weight4slope * weight4other) * 10000000.0
        return cst_dic
    
    def Rules4CstSurface(dic, work):
        txt = open(os.path.join(work, 'cst_surface.txt'), 'w')
        for key in dic.keys():
            txt.write(
                '{cat}  = {cst}\n'.format(cat=str(key), cst=str(dic[key]))
            )
        txt.close()
        return os.path.join(work, 'cst_surface.txt')
    
    """
    Prepare GRASS GIS Environment
    """
    workspace = os.path.dirname(grass_location)
    location = os.path.basename(grass_location)
    # Start GRASS GIS Engine
    grass_base = run_grass(workspace, location, dem, win_path=grass_path)
    import grass.script as grass
    import grass.script.setup as gsetup
    gsetup.init(grass_base, workspace, location, 'PERMANENT')
    
    # Import GRASS GIS Modules
    from gasp3.dt.to.shp         import grs_to_shp, shp_to_grs
    from gasp3.gt.spnlst.surf    import slope
    from gasp3.gt.mng.rst.rcls   import rcls_rst, interval_rules
    from gasp3.gt.mng.rst.rcls   import category_rules, set_null
    from gasp3.gt.mng.fld.grsfld import add_field
    from gasp3.gt.mng.grstbl     import update_table
    from gasp3.gt.anls.ovlay     import union
    from gasp3.dt.to.rst         import rst_to_grs, grs_to_rst
    from gasp3.gt.spnlst.local   import combine
    from gasp3.gt.spnlst.alg     import rstcalc
    from gasp3.gt.prop.rst       import raster_report
    from gasp3.gt.mng.rst        import mosaic_raster
    
    """Global variables"""
    # Workspace for temporary files
    wTmp = create_folder(os.path.join(workspace, 'tmp'))
    
    # Cellsize
    cellsize = float(get_cellsize(dem), gisApi='gdal')
    # Land Use Land Cover weights
    lulcWeight = lulc_weight(prod_lulc, cellsize)
    # Slope classes and weights
    slope_cls = get_slope_categories()
    
    """Make Cost Surface"""
    # Generate slope raster
    rst_to_grs(dem, 'dem')
    slope('dem', 'rst_slope', api="pygrass")
    
    # Reclassify Slope
    rulesSlope = interval_rules(slope_cls, os.path.join(wTmp, 'slope.txt'))
    reclassify('rst_slope', 'recls_slope', rulesSlope)
    
    # LULC - Dissolve, union with barriers and conversion to raster
    lulc_shp = edit_lulc(lulc, cls_lulc, lulc_weight)
    shp_to_grs(barr, 'barriers')
    union(lulc_shp['shp'], 'barriers', 'barrcos', api_gis="grass")
    update_table('barrcos', 'a_' + lulc_shp['fld'], 99, 'b_cat=1')
    shp_to_rst(
        'barrcos', 'a_' + lulc_shp['fld'], None, None, 'rst_barrcos',
        api='pygrass')
    
    # Reclassify this raster - convert the values 99 to NULL or NODATA
    grass_set_null('rst_barrcos', 99)
    
    # Add the roads layer to the GRASS GIS
    shp_to_grs(roads, 'rdv')
    if kph == 'pedestrian':
        add_field('rdv', 'foot', 'INT')
        update_table('rdv', 'foot', 50, 'foot IS NULL')
        shp_to_rst('rdv', 'foot', None, None, 'rst_rdv', api='pygrass')
    else:
        shp_to_rst('rdv', kph, None, None, 'rst_rdv', api='pygrass')
    
    # Merge LULC/BARR and Roads
    mosaic_raster('rst_rdv', 'rst_barrcos', 'rdv_barrcos')
    
    # Combine LULC/BARR/ROADS with Slope
    combine('recls_slope', 'rdv_barrcos', 'rst_combine', api="pygrass")
    
    """
    Estimating cost for every combination at rst_combine
    The order of the rasters on the following list has to be the same of
    GRASS Combine"""
    cst = combine_to_cost(
        'rst_combine', ['recls_slope', 'rdv_barrcos'],
        wTmp, slope_cls, lulc_weight, cell_size, kph
    )
    
    # Reclassify combined rst
    rulesSurface = category_rules(cst, os.path.join('r_surface.txt'))
    reclassify('rst_combine', 'cst_tmp', rulesSurface)
    rstcalc('cst_tmp / 10000000.0', 'cst_surface', api='pygrass')
    grs_to_rst('cst_surface', output)


def acumulated_cost(cst_surface, dest_pnt, cst_dist):
    """
    Uses a cost surface to estimate the time between each cell and the 
    close destination
    """
    
    from gasp3.gt.spnlst.alg import rstcalc
    from gasp3.gt.spnlst.dst import rcost
    from gasp3.dt.to.rst     import rst_to_grs, grs_to_rst
    from gasp3.dt.to.shp     import shp_to_grs
    
    # Add Cost Surface to GRASS GIS
    rst_to_grs(cst_surface, 'cst_surf')
    # Add Destination To GRASS
    shp_to_grs(dest_pnt, 'destination')
    # Execute r.cost
    rcost('cst_surf', 'destination', 'cst_dist')
    # Convert to minutes
    rstcalc('cst_dist / 60.0', 'CstDistMin', api="grass")
    # Export result
    grs_to_rst('CstDistMin', cst_dist)
    
    return cst_dist


def cstDistance_with_motorway(
    cst_surface, motorway, fld_motorway, nodes_start, nodes_end,
    pnt_destiny, grass_location, isolines
    ):
    """
    Produce a surface representing the acumulated cost of each cell to a
    destination point considering the false intersections caused by a non
    planar graph
    """
    
    import os
    from gasp3.pyt.oss import create_folder
    from gasp3.gt.prop.ff import drv_name
    from gasp3.gt.spnlst.local import rseries
    from gasp3.gt.spnlst.alg import rstcalc
    from gasp3.gt.spnlst.dst import rcost
    from gasp3.dt.to.rst import shp_to_rst, rst_to_grs
    from gasp3.gt.mng.sample import rst_val_to_points
    from pysage.tools_thru_api.gdal.ogr import OGR_CreateNewShape
    
    """
    Auxiliar Methods
    """
    def dist_to_nodes(pnt_shp, cstSurface, string, w):
        nodes = ogr.GetDriverByName(
            drv_name(pnt_shp)).Open(pnt_shp, 0)
        
        nodesLyr = nodes.GetLayer()
        
        c = 0
        dicNodes = {}
        for pnt in nodesLyr:
            geom = pnt.GetGeometryRef()
            point = geom.ExportToWkb()
            OGR_CreateNewShape(
                OGR_GetDriverName(pnt_shp),
                os.path.join(w, '{pnt}_{o}.shp'.format(pnt=string, o=str(c))),
                ogr.wkbPoint,
                [point]
            )
            FT_TF_GRASS(
                os.path.join(w, '{pnt}_{o}.shp'.format(pnt=string, o=str(c))),
                '{pnt}_{o}'.format(pnt=string, o=str(c)),
                'None'
            )
            GRASS_CostDistance(
                cstSurface,
                '{pnt}_{o}'.format(pnt=string, o=str(c)),
                'cst_{pnt}_{a}'.format(pnt=string, a=str(c))
            )
            dicNodes['{pnt}_{o}'.format(pnt=string, o=str(c))] = [os.path.join(w, '{pnt}_{o}.shp'.format(pnt=string, o=str(c))), 'cst_{pnt}_{a}'.format(pnt=string, a=str(c))]
            c+= 1
        return dicNodes    
    
    """GRASS GIS Configuration"""
    # Workspace for temporary files
    wTmp = create_folder(os.path.join(os.path.dirname(grass_location), 'tmp'))
    
    """Make Accessibility Map"""
    # Add Cost Surface to GRASS GIS
    convert(cst_surface, 'cst_surface')
    # Add Destination To GRASS
    convert(pnt_destiny, 'destination')
    
    # Run r.cost with only with a secundary roads network
    rcost('cst_surface', 'destination', 'cst_dist_secun')
    
    # We have to know if the path through motorway implies minor cost.
    # Add primary roads to grass
    convert(motorway, 'rdv_prim', 'None')
    
    # We need a cost surface only with the cost of motorway roads
    shp_to_rst('rdv_prim', fld_motorway, None, None, 'rst_rdv', api='pygrass')
    rstcalc(
        '(3600.0 * {cs}) / (rst_rdv * 1000.0)'.format(
            cs=get_cellsize(cst_surface, gisApi='gdal')
        ),
        'cst_motorway', api='grass'
    )
    
    # For each node of entrance into a motorway, we need to know:
    # - the distance to the entrance node;
    # - the distance between the entrance and every exit node
    # - the distance between the exit and the destination
    # Geting the distance to the entrance node
    entranceNodes = dist_to_nodes(
        nodes_start, 'cst_surface', 'start', wTmp
    )
    # Geting the distances to all entrance nodes
    exitNodes = dist_to_nodes(
        nodes_end, 'cst_surface', 'exit', wTmp
    )
    
    # Getting the values needed
    for start_pnt in entranceNodes.keys():
        for exit_pnt in exitNodes.keys():
            GRASS_CostDistance(
                'cst_motorway',
                exit_pnt,
                'cst2exit_{a}_{b}'.format(a=str(start_pnt[-1]), b=str(exit_pnt[-1]))
            )
            FT_TF_GRASS(
                'cst2exit_{a}_{b}'.format(a=str(start_pnt[-1]), b=str(exit_pnt[-1])),
                os.path.join(wTmp, 'cst2exit_{a}_{b}.tif'.format(a=str(start_pnt[-1]), b=str(exit_pnt[-1]))), 'None'
            )
            cst_start_exit = GDAL_ExtractValuesByPoint(
                entranceNodes[start_pnt][0],
                os.path.join(wTmp, 'cst2exit_{a}_{b}.tif'.format(a=str(start_pnt[-1]), b=str(exit_pnt[-1])))
            )
            if os.path.isfile(os.path.join(wTmp, exitNodes[exit_pnt][1] + '.tif')) == False:
                FT_TF_GRASS(
                    exitNodes[exit_pnt][1],
                    os.path.join(wTmp, exitNodes[exit_pnt][1] + '.tif'),
                    'None'
                )
            cst_exit_destination = GDAL_ExtractValuesByPoint(
                pnt_destiny,
                os.path.join(wTmp, exitNodes[exit_pnt][1] + '.tif')
            )
            GRASS_RasterCalculator(
                '{rst} + {a} + {b}'.format(rst=entranceNodes[start_pnt][1], a=str(cst_start_exit[0]), b=str(min(cst_exit_destination))),
                'cst_path_{a}_{b}'.format(a=str(start_pnt[-1]), b=str(exit_pnt[-1]))
            )
            lst_outputs.append('cst_path_{a}_{b}'.format(a=str(start_pnt[-1]), b=str(exit_pnt[-1])))
    lst_outputs.append('cst_dist_secun')
    rseries(lst_outputs, 'isocronas', 'minimum')

