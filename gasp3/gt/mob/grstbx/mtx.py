"""
Produce things related with accessibility
"""

import os

def prod_matrix(origins, destinations, networkGrs, speedLimitCol, onewayCol,
                thrdId="1", asCmd=None):
    """
    Get Matrix Distance:
    """
    
    from gasp.to.shp.grs       import shp_to_grs
    from gasp.cpu.grs.mng      import category
    from gasp.anls.exct        import sel_by_attr
    from gasp.mng.grstbl       import add_field, add_table, update_table
    from gasp.mob.grstbx       import network_from_arcs
    from gasp.mob.grstbx       import add_pnts_to_network
    from gasp.mob.grstbx       import run_allpairs
    from gasp.cpu.grs.mng.feat import geomattr_to_db
    from gasp.cpu.grs.mng.feat import copy_insame_vector
    from gasp.mng.gen          import merge_feat
    from gasp.prop.feat        import feat_count
    
    # Merge Origins and Destinations into the same Feature Class
    ORIGINS_NFEAT      = feat_count(origins, gisApi='pandas')
    DESTINATIONS_NFEAT = feat_count(destinations, gisApi='pandas')
    
    ORIGINS_DESTINATIONS = merge_feat(
        [origins, destinations], os.path.join(
            os.path.dirname(origins), "points_od_{}.shp".format(thrdId)
        ), api='pandas'
    )
    
    pointsGrs  = shp_to_grs(
        ORIGINS_DESTINATIONS, "points_od_{}".format(thrdId), asCMD=asCmd)
    
    # Connect Points to Network
    newNetwork = add_pnts_to_network(
        networkGrs, pointsGrs, "rdv_points_{}".format(thrdId), asCMD=asCmd
    )
    
    # Sanitize Network Table and Cost Columns
    newNetwork = category(
        newNetwork, "rdv_points_time_{}".format(thrdId), "add",
        LyrN="3", geomType="line", asCMD=asCmd
    )
    
    add_table(newNetwork, (
        "cat integer,kph double precision,length double precision,"
        "ft_minutes double precision,"
        "tf_minutes double precision,oneway text"
    ), lyrN=3, asCMD=asCmd)
    
    copy_insame_vector(
        newNetwork, "kph", speedLimitCol, 3, geomType="line", asCMD=asCmd
    ); copy_insame_vector(
        newNetwork, "oneway",  onewayCol, 3, geomType="line", asCMD=asCmd)
    
    geomattr_to_db(
        newNetwork, "length", "length", "line",
        createCol=False, unit="meters", lyrN=3, ascmd=asCmd
    )
    
    update_table(newNetwork, "kph", "3.6",  "kph IS NULL", lyrN=3, ascmd=asCmd)
    update_table(newNetwork, "kph", "3.6", "oneway = 'N'", lyrN=3, ascmd=asCmd)
    update_table(
        newNetwork, "ft_minutes",
        "(length * 60) / (kph * 1000.0)",
        "ft_minutes IS NULL", lyrN=3, ascmd=asCmd
    ); update_table(
        newNetwork, "tf_minutes",
        "(length * 60) / (kph * 1000.0)",
        "tf_minutes IS NULL", lyrN=3, ascmd=asCmd
    )
    
    # Exagerate Oneway's
    update_table(
        newNetwork, "ft_minutes", "1000", "oneway = 'TF'", lyrN=3, ascmd=asCmd
    ); update_table(
        newNetwork, "tf_minutes", "1000", "oneway = 'FT'", lyrN=3, ascmd=asCmd)
    
    # Produce matrix
    matrix = run_allpairs(
        newNetwork, "ft_minutes", "tf_minutes",
        'result_{}'.format(thrdId), arcLyr=3, nodeLyr=2, asCMD=asCmd
    )
    
    # Exclude unwanted OD Pairs
    q = "({}) AND ({})".format(
        " OR ".join(["from_cat={}".format(
            str(i+1)) for i in range(ORIGINS_NFEAT)
        ]),
        " OR ".join(["to_cat={}".format(
            str(ORIGINS_NFEAT + i + 1)) for i in range(DESTINATIONS_NFEAT)
        ])
    )
    
    matrix_sel = sel_by_attr(
        matrix, q, "sel_{}".format(matrix),
        geomType="line", lyrN=3, asCMD=asCmd
    )
    
    add_field(matrix_sel, "from_fid", "INTEGER", lyrN=3, asCMD=asCmd)
    add_field(matrix_sel,   "to_fid", "INTEGER", lyrN=3, asCMD=asCmd)
    
    update_table(
        matrix_sel, "from_fid",
        "from_cat - 1", "from_fid IS NULL", lyrN=3, ascmd=asCmd
    ); update_table(
        matrix_sel, "to_fid", 
        "to_cat - {} - 1".format(str(ORIGINS_NFEAT)),
        "to_fid IS NULL", lyrN=3, ascmd=asCmd
    )
    
    return matrix_sel


def matrix_od(origins, destinations, networkShp, speedLimitCol, onewayCol,
              grsWorkspace, grsLocation, outputShp):
    """
    Produce matrix OD using GRASS GIS
    """
    
    from gasp.oss     import get_filename
    from gasp.session import run_grass
    
    # Open an GRASS GIS Session
    gbase = run_grass(
        grsWorkspace, grassBIN="grass74",
        location=grsLocation, srs=networkShp
    )
    
    import grass.script       as grass
    import grass.script.setup as gsetup
    
    gsetup.init(gbase, grsWorkspace, grsLocation, 'PERMANENT')
    
    # Import GRASS GIS Module
    from gasp.to.shp.grs import shp_to_grs
    
    # Add Data to GRASS GIS
    rdvMain = shp_to_grs(networkShp, get_filename(
        networkShp, forceLower=True))
    
    """Get matrix distance:"""
    MATRIX_OD = prod_matrix(
        origins, destinations, rdvMain, speedLimitCol, onewayCol
    )
    
    return grass_converter(MATRIX_OD, outputShp, geom_type="line", lyrN=3)

def thrd_matrix_od(origins, destinationShp, network, costCol, oneway,
                   grsWork, grsLoc, output):
    """
    Produce matrix OD using GRASS GIS - Thread MODE
    
    PROBLEM:
    * O programa baralha-se todo porque ha muitas sessoes do grass a serem 
    executadas. E preciso verificar se e possivel segregar as varias sessoes
    do grass
    """
    
    from threading      import Thread
    from gasp.session   import run_grass
    from gasp.oss       import get_filename
    from gasp.oss.ops   import create_folder
    from gasp.mng.split import splitShp_by_range
    from gasp.mng.gen   import merge_feat
    
    # SPLIT ORIGINS IN PARTS
    originsFld = create_folder(os.path.join(grsWork, 'origins_parts'))
    
    originsList = splitShp_by_range(origins, 100, originsFld)
    
    
    gbase = run_grass(
        grsWork, grassBIN="grass74", location=grsLoc, srs=network
    )
    
    import grass.script       as grass
    import grass.script.setup as gsetup
    
    gsetup.init(gbase, grsWork, grsLoc, 'PERMANENT')
    
    from gasp.to.shp.grs import shp_to_grs
    from gasp.to.shp.grs import grs_to_shp
    # Add Data to GRASS GIS
    rdvMain = shp_to_grs(network, get_filename(
        network, forceLower=True), asCMD=True)
    
    RESULTS = []
    R_FOLDER = create_folder(os.path.join(grsWork, 'res_parts'))
    
    def __prod_mtxod(O, D, THRD):
        result_part = prod_matrix(
            O, D, rdvMain, costCol, oneway, thrdId=THRD, asCmd=True
        )
        
        shp = shp_to_grs(
            result_part, os.path.join(R_FOLDER, result_part + '.shp'),
            geom_type="line", lyrN=3, asCMD=True
        )
        
        RESULTS.append(shp)
    
    thrds = []
    for i in range(len(originsList)):
        thrds.append(Thread(
            name='tk-{}'.format(str(i)), target=__prod_mtxod,
            args=(originsList[i], destinationShp, str(i))
        ))
    
    for t in thrds:
        t.start()
    
    for t in thrds:
        t.join()
    
    merge_feat(RESULTS, output, api='pandas')
    
    return output


def bash_matrix_od(origins, destinationShp, network, costCol, oneway,
                   grsWork, output):
    """
    Produce matrix OD using GRASS GIS - BASH MODE
    """
    
    from gasp.session   import run_grass
    from gasp.oss       import get_filename
    from gasp.oss.ops   import create_folder
    from gasp.mng.split import splitShp_by_range
    from gasp.mng.gen   import merge_feat
    
    # SPLIT ORIGINS IN PARTS
    originsFld = create_folder(os.path.join(grsWork, 'origins_parts'))
    
    originsList = splitShp_by_range(origins, 100, originsFld)
    
    # Open an GRASS GIS Session
    gbase = run_grass(
        grsWork, grassBIN="grass76", location=grsLoc, srs=network
    )
    
    import grass.script       as grass
    import grass.script.setup as gsetup
    
    RESULTS = []
    R_FOLDER = create_folder(os.path.join(grsWork, 'res_parts'))
    
    for e in range(len(originsList)):
        gsetup.init(gbase, grsWork, "grs_loc_{}".format(e), 'PERMANENT')
    
        from gasp.to.shp.grs import shp_to_grs, grs_to_shp
    
        # Add Data to GRASS GIS
        rdvMain = shp_to_grs(network, get_filename(
            network, forceLower=True))
        
        # Produce Matrix
        result_part = prod_matrix(
            originsList[e], destinationShp, rdvMain, costCol, oneway
        )
        
        # Export Result
        shp = grs_to_shp(
            result_part, os.path.join(R_FOLDER, result_part + '.shp'),
            geom_type="line", lyrN=3
        )
        
        RESULTS.append(shp)
    
    merge_feat(RESULTS, output, api='pandas')
    
    return output

