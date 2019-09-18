def distance_between_catpoints(srcShp, facilitiesShp, networkShp, speedLimitCol,
                     onewayCol, grsWorkspace, grsLocation, outputShp):
    """
    Path bet points
    
    TODO: Work with files with cat
    """
    
    import os
    from gasp3.pyt.oss      import get_filename
    from gasp3.gt.wenv.grs  import run_grass
    from gasp3.gt.mng.gen   import merge_feat
    from gasp3.gt.prop.feat import feat_count
    
    # Merge Source points and Facilities into the same Feature Class
    SRC_NFEAT      = feat_count(srcShp, gisApi='pandas')
    FACILITY_NFEAT = feat_count(facilitiesShp, gisApi='pandas')
    
    POINTS = merge_feat([srcShp, facilitiesShp],
        os.path.join(os.path.dirname(outputShp), "points_net.shp"),
        api='pandas'
    )
    
    # Open an GRASS GIS Session
    gbase = run_grass(
        grsWorkspace, grassBIN="grass76",
        location=grsLocation, srs=networkShp
    )
    
    import grass.script       as grass
    import grass.script.setup as gsetup
    gsetup.init(gbase, grsWorkspace, grsLocation, 'PERMANENT')
    
    # Import GRASS GIS Module
    from gasp3.gt.to.shp         import shp_to_grs, grs_to_shp
    from gasp3.gt.mng.tbl        import geomattr_to_db, copy_insame_vector
    from gasp3.gt.mng.grsv       import category
    from gasp3.gt.mng.grstbl     import add_table, update_table
    from gasp3.gt.mng.fld.grsfld import add_field
    from gasp3.gt.mob.grs        import network_from_arcs
    from gasp3.gt.mob.grs        import add_pnts_to_network
    from gasp3.gt.mob.grs        import netpath
    
    # Add Data to GRASS GIS
    rdvMain = shp_to_grs(networkShp, get_filename(
        networkShp, forceLower=True))
    pntShp  = shp_to_grs(POINTS, "points_net")
    
    """Get closest facility layer:"""
    # Connect Points to Network
    newNetwork = add_pnts_to_network(rdvMain, pntShp, "rdv_points")
    
    # Sanitize Network Table and Cost Columns
    newNetwork = category(
        newNetwork, "rdv_points_time", "add",
        LyrN="3", geomType="line"
    )
    
    add_table(newNetwork, (
        "cat integer,kph double precision,length double precision,"
        "ft_minutes double precision,"
        "tf_minutes double precision,oneway text"
    ), lyrN=3)
    
    copy_insame_vector(newNetwork, "kph", speedLimitCol, 3, geomType="line")
    copy_insame_vector(newNetwork, "oneway",  onewayCol, 3, geomType="line")
    
    geomattr_to_db(
        newNetwork, "length", "length", "line",
        createCol=False, unit="meters", lyrN=3
    )
    
    update_table(newNetwork, "kph", "3.6", "kph IS NULL", lyrN=3)
    update_table(
        newNetwork, "ft_minutes",
        "(length * 60) / (kph * 1000.0)",
        "ft_minutes IS NULL", lyrN=3
    ); update_table(
        newNetwork, "tf_minutes",
        "(length * 60) / (kph * 1000.0)",
        "tf_minutes IS NULL", lyrN=3
    )
    
    # Exagerate Oneway's
    update_table(newNetwork, "ft_minutes", "1000", "oneway = 'TF'", lyrN=3)
    update_table(newNetwork, "tf_minutes", "1000", "oneway = 'FT'", lyrN=3)
    
    # Produce result
    result = netpath(
        newNetwork, "ft_minutes", "tf_minutes", get_filename(outputShp),
        arcLyr=3, nodeLyr=2
    )
    
    return grs_to_shp(result, outputShp, geomType="line", lyrN=3)
