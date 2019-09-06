"""
Rule 6
"""

import os
from gasp.osm2lulc.var import DB_SCHEMA

def rst_pnt_to_build(osmLink, pntTable, polyTable, api_db='SQLITE'):
    """
    Replace buildings with tag yes using the info in the Points Layer
    
    Only used for URBAN ATLAS and CORINE LAND COVER
    """
    
    import datetime
    from gasp.sql.mng.tbl    import row_num as cnt_row
    from gasp.fm.sql         import query_to_df
    if api_db == 'POSTGIS':
        from gasp.to.shp.grs import psql_to_grs as db_to_shp
    else:
        from gasp.to.shp.grs import sqlite_to_shp as db_to_shp
    from gasp.sql.anls.ovlay import sgbd_get_feat_within
    from gasp.sql.anls.ovlay import sgbd_get_feat_not_within
    from gasp.to.rst         import shp_to_rst
    
    time_a = datetime.datetime.now().replace(microsecond=0)
    new_build = sgbd_get_feat_within(
        osmLink, (
            "(SELECT buildings AS pnt_build, geometry AS pnt_geom "
            "FROM {} WHERE buildings IS NOT NULL)"
        ).format(pntTable), "pnt_geom", (
            "(SELECT buildings AS poly_build, geometry AS poly_geom "
            "FROM {} WHERE buildings IS NOT NULL)"
        ).format(polyTable), "poly_geom", "new_buildings",
        inTblCols="pnt_build AS cls", withinCols="poly_geom AS geometry",
        outTblIsFile=None,
        apiToUse="OGR_SPATIALITE" if api_db != "POSTGIS" else api_db
    )
    time_b = datetime.datetime.now().replace(microsecond=0)
    
    yes_build = sgbd_get_feat_not_within(
        osmLink, (
            "(SELECT buildings AS poly_build, geometry AS poly_geom "
            "FROM {} WHERE buildings IS NOT NULL)"
        ).format(polyTable), "poly_geom", (
            "(SELECT buildings AS pnt_build, geometry AS pnt_geom "
            "FROM {} WHERE buildings IS NOT NULL)"
        ).format(pntTable), "pnt_geom", "yes_builds",
        inTblCols="poly_geom AS geometry, 11 AS cls",
        outTblIsFile=None,
        apiToUse="OGR_SPATIALITE" if api_db != "POSTGIS" else api_db
    )
    time_c = datetime.datetime.now().replace(microsecond=0)
    
    resLayers = {}
    N11 = cnt_row(osmLink, yes_build,
        api='psql' if api_db == 'POSTGIS' else 'sqlite')
    time_d = datetime.datetime.now().replace(microsecond=0)
    
    if N11:
        # Data to GRASS GIS
        grsBuild11 = db_to_shp(
            osmLink, yes_build, "yes_builds", notTable=True, filterByReg=True
        )
        time_f = datetime.datetime.now().replace(microsecond=0)
        
        # To raster
        rstBuild11 = shp_to_rst(
            grsBuild11, 11, None, None, "rst_builds11", api="grass")
        time_g = datetime.datetime.now().replace(microsecond=0)
        
        resLayers[11] = [rstBuild11]
    
    else:
        time_f = None; time_g = None
    
    # Add data into GRASS GIS
    lulcCls = query_to_df(
        osmLink, "SELECT cls FROM {} GROUP BY cls".format(new_build),
        db_api='psql' if api_db == 'POSTGIS' else 'sqlite'
    ).cls.tolist()
    
    timeGasto = {
        0 : ('intersect', time_b - time_a),
        1 : ('disjoint', time_c - time_b),
        2 : ('count_b11', time_d - time_c),
        3 : None if not time_f else ('import_b11', time_f - time_d),
        4 : None if not time_g else ('torst_b11', time_g - time_f),
    }
    tk = 5
    for cls in lulcCls:
        time_x = datetime.datetime.now().replace(microsecond=0)
        shp = db_to_shp(
            osmLink, new_build, "nbuild_{}".format(str(cls)),
            "cls = {}".format(cls), notTable=True, filterByReg=True
        )
        time_y = datetime.datetime.now().replace(microsecond=0)
        
        rstb = shp_to_rst(
            shp, int(cls), None, None, "rst_nbuild_{}".format(str(cls)),
            api="grass"
        )
        time_z = datetime.datetime.now().replace(microsecond=0)
        
        if int(cls) == 11 and int(cls) in resLayers:
            resLayers[int(cls)].append(rstb)
        
        else:
            resLayers[int(cls)] = [rstb]
        
        timeGasto[tk]     = ('import_bn{}'.format(cls), time_y - time_x)
        timeGasto[tk + 1] = ('torst_bn{}'.format(cls), time_z - time_y)
        
        tk += 2
    
    return resLayers, timeGasto


def vector_assign_pntags_to_build(osmdb, pntTable, polyTable, apidb='SQLITE'):
    """
    Replace buildings with tag yes using the info in the Points Layer
    
    Only used for URBAN ATLAS and CORINE LAND COVER
    """
    
    import datetime
    from gasp.sql.mng.tbl    import row_num as cnt_row
    if apidb != "POSTGIS":
        from gasp.to.shp.grs import sqlite_to_shp as db_to_shp
    else:
        from gasp.to.shp.grs import psql_to_grs as db_to_shp
    from gasp.sql.anls.ovlay import sgbd_get_feat_within
    from gasp.sql.anls.ovlay import sgbd_get_feat_not_within
    from gasp.mng.genze      import dissolve
    from gasp.mng.grstbl     import add_table
    
    time_a = datetime.datetime.now().replace(microsecond=0)
    new_build = sgbd_get_feat_within(
        osmdb, (
            "(SELECT buildings AS pnt_build, geometry AS pnt_geom "
            "FROM {} WHERE buildings IS NOT NULL)"
        ).format(pntTable), "pnt_geom", (
            "(SELECT buildings AS poly_build, geometry AS poly_geom "
            "FROM {} WHERE buildings IS NOT NULL)"
        ).format(polyTable), "poly_geom", "new_buildings",
        inTblCols="pnt_build AS cls", withinCols="poly_geom AS geometry",
        outTblIsFile=None,
        apiToUse="OGR_SPATIALITE" if apidb != "POSTGIS" else apidb
    )
    time_b = datetime.datetime.now().replace(microsecond=0)
    
    yes_build = sgbd_get_feat_not_within(
        osmdb, (
            "(SELECT buildings AS poly_build, geometry AS poly_geom "
            "FROM {} WHERE buildings IS NOT NULL)"
        ).format(polyTable), "poly_geom", (
            "(SELECT buildings AS pnt_build, geometry AS pnt_geom "
            "FROM {} WHERE buildings IS NOT NULL)"
        ).format(pntTable), "pnt_geom", "yes_builds",
        inTblCols="poly_geom AS geometry, 11 AS cls", outTblIsFile=None,
        apiToUse="OGR_SPATIALITE" if apidb != "POSTGIS" else apidb
    )
    time_c = datetime.datetime.now().replace(microsecond=0)
    
    N12 = cnt_row(osmdb, new_build, api='psql' if apidb == 'POSTGIS' else 'sqlite')
    time_d = datetime.datetime.now().replace(microsecond=0)
    N11 = cnt_row(osmdb, yes_build, api='psql' if apidb == 'POSTGIS' else 'sqlite')
    time_e = datetime.datetime.now().replace(microsecond=0)
    
    if N11:
        # Add data into grasss
        grsBuild11 = db_to_shp(osmdb, yes_build, "yes_builds", filterByReg=True)
        time_f = datetime.datetime.now().replace(microsecond=0)
        
        # Dissolve
        dissVect = dissolve(
            grsBuild11, "dss_{}".format(grsBuild11),
            'cls', api="grass"
        )
        
        add_table(dissVect, None, lyrN=1, asCMD=True)
        time_g = datetime.datetime.now().replace(microsecond=0)
    else:
        dissVect = None
        time_f = None; time_g = None
    
    if N12:
        # Add data into GRASS GIS
        grsBuild12 = db_to_shp(osmdb, new_build, "pnt_build", filterByReg=True)
        
        time_h = datetime.datetime.now().replace(microsecond=0)
        
        # Dissolve
        dissVect12 = dissolve(
            grsBuild12, "dss_{}".format(grsBuild12),
            'cls', api="grass"
        )
        
        add_table(dissVect12, None, lyrN=1, asCMD=True)
        time_i = datetime.datetime.now().replace(microsecond=0)
    
    else:
        dissVect12 = None
        time_h = None; time_i = None
    
    return dissVect, dissVect12, {
        0 : ('intersect', time_b - time_a),
        1 : ('disjoint', time_c - time_b),
        2 : ('count_b12', time_d - time_c),
        3 : ('count_b11', time_e - time_d),
        4 : None if not time_f else ('import_b11', time_f - time_e),
        5 : None if not time_g else ('dissolve_b11', time_g - time_f),
        6 : None if not time_h else (
            'import_b12', time_h - time_g if time_g else time_h - time_e),
        7 : None if not time_i else ('dissolve_b12', time_i - time_h)
    }


def num_assign_builds(osmLink, pntTbl, polTbl, folder, cells, srscode, rstT,
                      apidb='SQLITE'):
    """
    Replace buildings with tag yes using the info in the Points Layer
    
    Only used for URBAN ATLAS and CORINE LAND COVER
    """
    
    import datetime
    from threading           import Thread
    if apidb == 'SQLITE':
        from gasp.anls.exct  import sel_by_attr
    else:
        from gasp.to.shp     import psql_to_shp as sel_by_attr
    from gasp.sql.anls.ovlay import sgbd_get_feat_within
    from gasp.sql.anls.ovlay import sgbd_get_feat_not_within
    from gasp.fm.sql         import query_to_df
    from gasp.to.rst         import shp_to_rst
    
    time_a = datetime.datetime.now().replace(microsecond=0)
    build12 = sgbd_get_feat_within(
        osmLink, (
            "(SELECT buildings as pnt_build, geometry AS pnt_geom "
            "FROM {} WHERE buildings IS NOT NULL)"
        ).format(pntTbl), "pnt_geom", (
            "(SELECT buildings AS poly_build, geometry AS poly_geom "
            "FROM {} WHERE buildings IS NOT NULL)"
        ).format(polTbl), "poly_geom", "info_builds",
        inTblCols="pnt_build AS cls", withinCols="poly_geom AS geometry",
        outTblIsFile=None,
        apiToUse="OGR_SPATIALITE" if apidb != "POSTGIS" else apidb
    )
    time_b = datetime.datetime.now().replace(microsecond=0)
    
    build11 = sgbd_get_feat_not_within(
        osmLink, (
            "(SELECT building AS poly_build, geometry AS poly_geom "
            "FROM {} WHERE buildings IS NOT NULL)"
        ).format(polTbl), "poly_geom", (
            "(SELECT buildings AS pnt_build, geometry AS pnt_geom "
            "FROM {} WHERE buildings IS NOT NULL)"
        ).format(pntTbl), "pnt_geom",
        os.path.join(folder, 'unkbuilds.shp'),
        inTblCols="poly_geom AS geometry, 11 AS cls", outTblIsFile=True,
        apiToUse="OGR_SPATIALITE" if apidb != "POSTGIS" else apidb
    )
    time_c = datetime.datetime.now().replace(microsecond=0)
    
    timeGasto = {
        0 : ('intersect', time_b - time_a),
        1 : ('disjoin', time_c - time_b)
    }
    
    resLyr = {}
    def toRaster(buildShp, cls):
        if not os.path.exists(buildShp): return
        
        # To Raster
        time_x = datetime.datetime.now().replace(microsecond=0)
        rstbuild = shp_to_rst(
            buildShp, None, cells, 0,
            os.path.join(folder, 'rst_build_{}.tif'.format(cls)),
            srscode, rstT, api='gdal'
        )
        time_y = datetime.datetime.now().replace(microsecond=0)
        
        resLyr[33] = rstbuild
        
        timeGasto[33] = ('to_rst_{}'.format(cls), time_y - time_x)
    
    def build12_torst(buildTbl):
        LulcCls = query_to_df(
            osmLink, "SELECT cls FROM {} GROUP BY cls".format(buildTbl),
            db_api='psql' if apidb == 'POSTGIS' else 'sqlite'
        ).cls.tolist()
        
        for lulc_cls in LulcCls:
            time_m = datetime.datetime.now().replace(microsecond=0)
            
            # To SHP
            if apidb == 'SQLITE':
                shpB = sel_by_attr(
                    osmLink, "SELECT * FROM {} WHERE cls={}".format(
                        buildTbl, str(lulc_cls)
                    ), os.path.join(folder, 'nshp_build_{}.shp'.format(lulc_cls)),
                    api_gis='ogr'
                )
            
            else:
                shpB = sel_by_attr(
                    osmLink, "SELECT * FROM {} WHERE cls={}".format(
                        buildTbl, str(lulc_cls)
                    ), os.path.join(folder, 'nshp_build_{}.shp'.format(lulc_cls)),
                    api='pgsql2shp', geom_col="geometry", tableIsQuery=True
                )
            time_n = datetime.datetime.now().replace(microsecond=0)
            
            # To RST
            brst = shp_to_rst(
                shpB, None, cells, 0,
                os.path.join(folder, 'nrst_build_{}.tif'.format(lulc_cls)),
                srscode, rstT, api='gdal'
            )
            time_o = datetime.datetime.now().replace(microsecond=0)
            
            resLyr[int(lulc_cls)] = [brst]
            
            timeGasto[int(lulc_cls)] = ('to_shp_{}'.format(str(lulc_cls)), time_n - time_m)
            timeGasto[int(lulc_cls) + 1] = (
                'to_rst_n_{}'.format(str(lulc_cls)), time_o - time_n
            )
    
    thrds = [
        Thread(name='builds-th-11', target=toRaster, args=(build11, 11)),
        Thread(name='builds-th-12', target=build12_torst, args=(build12,))
    ]
    
    for t in thrds: t.start()
    for t in thrds: t.join()
    
    if 33 in resLyr:
        if 11 in resLyr:
            resLyr[11].append(resLyr[33])
        
        else:
            resLyr[11] = [resLyr[33]]
            
        del resLyr[33]
    
    return resLyr, timeGasto

