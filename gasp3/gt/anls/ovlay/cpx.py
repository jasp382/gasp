"""
Complex Overlay Tools
"""


def check_shape_diff(SHAPES_TO_COMPARE, OUT_FOLDER, REPORT, conPARAM, DB, SRS_CODE,
                     GIS_SOFTWARE="GRASS", GRASS_REGION_TEMPLATE=None):
    """
    Script to check differences between pairs of Feature Classes
    
    Suponha que temos diversas Feature Classes (FC) e que cada uma delas
    possui um determinado atributo; imagine tambem que,
    considerando todos os pares possiveis entre estas FC,
    se pretende comparar as diferencas na distribuicao dos valores
    desse atributo em cada par.
    
    * Dependencias:
    - ArcGIS;
    - GRASS;
    - PostgreSQL;
    - PostGIS.
    
    * GIS_SOFTWARE Options:
    - ARCGIS;
    - GRASS.
    """
    
    import datetime
    import os;             import pandas
    from gasp3.dt.fm.sql import query_to_df
    from gasp3.dt.to import db_to_tbl, df_to_db
    from gasp3.dt.to.shp import shp_to_shp, psql_to_shp, rst_to_polyg
    from gasp3.dt.to.sql import shp_to_psql
    from gasp3.gt.prop.ff import check_isRaster
    from gasp3.pyt.oss import get_filename
    from gasp3.sql.mng.db import create_db
    from gasp3.sql.mng.tbl import tbls_to_tbl, q_to_ntbl
    from gasp3.sql.mng.geom import fix_geom, check_geomtype_in_table
    from gasp3.sql.mng.geom import select_main_geom_type
    
    # Check if folder exists, if not create it
    if not os.path.exists(OUT_FOLDER):
        from gasp.pyt.oss import create_folder
        create_folder(OUT_FOLDER, overwrite=None)
    else:
        raise ValueError('{} already exists!'.format(OUT_FOLDER))
    
    # Start GRASS GIS Session if GIS_SOFTWARE == GRASS
    if GIS_SOFTWARE == "GRASS":
        if not GRASS_REGION_TEMPLATE:
            raise ValueError(
                'To use GRASS GIS you need to specify GRASS_REGION_TEMPLATE'
            )
        
        from gasp3.gt.wenv.grs import run_grass
        
        gbase = run_grass(
            OUT_FOLDER, grassBIN='grass76', location='shpdif',
            srs=GRASS_REGION_TEMPLATE
        )
        
        import grass.script as grass
        import grass.script.setup as gsetup
        
        gsetup.init(gbase, OUT_FOLDER, 'shpdif', 'PERMANENT')
        
        from gasp3.dt.to.shp         import shp_to_grs, grs_to_shp
        from gasp3.dt.to.rst         import rst_to_grs
        from gasp3.gt.mng.fld.grsfld import rename_col
        from gasp3.gt.mng.fld.ogrfld import rename_column
    
    # Convert to SHAPE if file is Raster
    # Import to GRASS GIS if GIS SOFTWARE == GRASS
    i = 0
    _SHP_TO_COMPARE = {}
    for s in SHAPES_TO_COMPARE:
        isRaster = check_isRaster(s)
    
        if isRaster:
            if GIS_SOFTWARE == "ARCGIS":
                d = rst_to_polyg(s, os.path.join(
                    os.path.dirname(s), get_filename(s) + '.shp'
                ), gisApi='arcpy')
        
                _SHP_TO_COMPARE[d] = "gridcode"
            
            elif GIS_SOFTWARE == "GRASS":
                # To GRASS
                rstName = get_filename(s)
                inRst   = rst_to_grs(s, "rst_" + rstName, as_cmd=True)
                # To Raster
                d       = rst_to_polyg(inRst, rstName,
                    rstColumn="lulc_{}".format(i), gisApi="grasscmd")
                
                # Export Shapefile
                shp = grs_to_shp(
                    d, os.path.join(OUT_FOLDER, d + '.shp'), "area")
                
                _SHP_TO_COMPARE[shp] = "lulc_{}".format(i)
    
        else:
            if GIS_SOFTWARE == "ARCGIS":
                _SHP_TO_COMPARE[s] = SHAPES_TO_COMPARE[s]
            
            elif GIS_SOFTWARE == "GRASS":
                # To GRASS
                grsV = shp_to_grs(s, get_filename(s), asCMD=True)
                
                # Change name of column with comparing value
                rename_col(
                    grsV, SHAPES_TO_COMPARE[s],
                    "lulc_{}".format(i), as_cmd=True
                )
                
                # Export
                shp = grs_to_shp(
                    grsV, os.path.join(OUT_FOLDER, grsV + '_rn.shp'), "area")
                
                _SHP_TO_COMPARE[shp] = "lulc_{}".format(i)
        
        i += 1
    
    SHAPES_TO_COMPARE = _SHP_TO_COMPARE
    if GIS_SOFTWARE == "ARCGIS":
        from gasp.cpu.arcg.mng.fld    import calc_fld
        from gasp.cpu.arcg.mng.wspace import create_geodb
        from gasp.mng.gen             import copy_feat
        
        # Sanitize data and Add new field
        __SHAPES_TO_COMPARE = {}
        i = 0
    
        # Create GeoDatabase
        geodb = create_geodb(OUT_FOLDER, 'geo_sanitize')
    
        """ Sanitize Data """
        for k in SHAPES_TO_COMPARE:
            # Send data to GeoDatabase only to sanitize
            newFc = shp_to_shp(
                k, os.path.join(geodb, get_filename(k)), gisApi='arcpy')
    
            # Create a copy to change
            newShp = copy_feat(newFc,
                 os.path.join(OUT_FOLDER, os.path.basename(k)), gisApi='arcpy'
            )
    
            # Sanitize field name with interest data
            NEW_FLD = "lulc_{}".format(i)
            calc_fld(
                newShp, NEW_FLD, "[{}]".format(SHAPES_TO_COMPARE[k]),
                isNewField={"TYPE" : "INTEGER", "LENGTH" : 5, "PRECISION" : ""}
            )
    
            __SHAPES_TO_COMPARE[newShp] = NEW_FLD
    
            i += 1
    
    else:
        __SHAPES_TO_COMPARE = SHAPES_TO_COMPARE
    
    # Create database
    conPARAM["DATABASE"] = create_db(conPARAM, DB)
    
    """ Union SHAPEs """
    
    UNION_SHAPE = {}
    FIX_GEOM = {}
    
    def fix_geometry(shp):
        # Send data to PostgreSQL
        nt = shp_to_psql(conPARAM, shp, SRS_CODE, api='shp2pgsql')
    
        # Fix data
        corr_tbl = fix_geom(
            conPARAM, nt, "geom", "corr_{}".format(nt),
            colsSelect=['gid', __SHAPES_TO_COMPARE[shp]]
        )
    
        # Check if we have multiple geometries
        geomN = check_geomtype_in_table(conPARAM, corr_tbl)
    
        if geomN > 1:
            corr_tbl = select_main_geom_type(
                conPARAM, corr_tbl, "corr2_{}".format(nt))
    
        # Export data again
        newShp = psql_to_shp(
            conPARAM, corr_tbl,
            os.path.join(OUT_FOLDER, corr_tbl + '.shp'),
            api='pgsql2shp', geom_col='geom'
        )
        
        return newShp
    
    SHPS = __SHAPES_TO_COMPARE.keys()
    for i in range(len(SHPS)):
        for e in range(i + 1, len(SHPS)):
            if GIS_SOFTWARE == 'ARCGIS':
                # Try the union thing
                unShp = union(SHPS[i], SHPS[e], os.path.join(
                    OUT_FOLDER, "un_{}_{}.shp".format(i, e)
                ), api_gis="arcpy")
        
                # See if the union went all right
                if not os.path.exists(unShp):
                    # Union went not well
            
                    # See if geometry was already fixed
                    if SHPS[i] not in FIX_GEOM:
                        # Fix SHPS[i] geometry
                        FIX_GEOM[SHPS[i]] = fix_geometry(SHPS[i])
            
                    if SHPS[e] not in FIX_GEOM:
                        FIX_GEOM[SHPS[e]] = fix_geometry(SHPS[e])
            
                    # Run Union again
                    unShp = union(FIX_GEOM[SHPS[i]], FIX_GEOM[SHPS[e]], os.path.join(
                        OUT_FOLDER, "un_{}_{}_f.shp".format(i, e)
                    ), api_gis="arcpy")
            
            elif GIS_SOFTWARE == "GRASS":
                # Optimized Union
                print("Union between {} and {}".format(SHPS[i], SHPS[e]))
                time_a = datetime.datetime.now().replace(microsecond=0)
                __unShp = optimized_union_anls(
                    SHPS[i], SHPS[e],
                    os.path.join(OUT_FOLDER, "un_{}_{}.shp".format(i, e)),
                    GRASS_REGION_TEMPLATE, SRS_CODE,
                    os.path.join(OUT_FOLDER, "work_{}_{}".format(i, e)),
                    multiProcess=True
                )
                time_b = datetime.datetime.now().replace(microsecond=0)
                print(time_b - time_a)
                
                # Rename cols
                unShp = rename_column(__unShp, {
                    "a_" + __SHAPES_TO_COMPARE[SHPS[i]] : __SHAPES_TO_COMPARE[SHPS[i]],
                    "b_" + __SHAPES_TO_COMPARE[SHPS[e]] : __SHAPES_TO_COMPARE[SHPS[e]]
                }, os.path.join(OUT_FOLDER, "un_{}_{}_rn.shp".format(i, e)))
            
            UNION_SHAPE[(SHPS[i], SHPS[e])] = unShp
    
    # Send data one more time to postgresql
    SYNTH_TBL = {}
    
    for uShp in UNION_SHAPE:
        # Send data to PostgreSQL
        union_tbl = shp_to_psql(
            conPARAM, UNION_SHAPE[uShp], SRS_CODE, api='shp2pgsql'
        )
        
        # Produce table with % of area equal in both maps
        areaMapTbl = q_to_ntbl(conPARAM, "{}_syn".format(union_tbl), (
            "SELECT CAST('{lulc_1}' AS text) AS lulc_1, "
            "CAST('{lulc_2}' AS text) AS lulc_2, "
            "round("
                "CAST(SUM(g_area) / 1000000 AS numeric), 4"
            ") AS agree_area, round("
                "CAST((SUM(g_area) / MIN(total_area)) * 100 AS numeric), 4"
            ") AS agree_percentage, "
            "round("
                "CAST(MIN(total_area) / 1000000 AS numeric), 4"
            ") AS total_area FROM ("
                "SELECT {map1_cls}, {map2_cls}, ST_Area(geom) AS g_area, "
                "CASE "
                    "WHEN {map1_cls} = {map2_cls} "
                    "THEN 1 ELSE 0 "
                "END AS isthesame, total_area FROM {tbl}, ("
                    "SELECT SUM(ST_Area(geom)) AS total_area FROM {tbl}"
                ") AS foo2"
            ") AS foo WHERE isthesame = 1 "
            "GROUP BY isthesame"
        ).format(
            lulc_1 = get_filename(uShp[0]), lulc_2 = get_filename(uShp[1]),
            map1_cls = __SHAPES_TO_COMPARE[uShp[0]],
            map2_cls = __SHAPES_TO_COMPARE[uShp[1]],
            tbl = union_tbl
        ), api='psql')
        
        # Produce confusion matrix for the pair in comparison
        lulcCls = query_to_df(conPARAM, (
            "SELECT fcol FROM ("
                "SELECT CAST({map1_cls} AS text) AS fcol FROM {tbl} "
                "GROUP BY {map1_cls} "
                "UNION ALL SELECT CAST({map2_cls} AS text) FROM {tbl} "
                "GROUP BY {map2_cls}"
            ") AS foo GROUP BY fcol ORDER BY fcol"
        ).format(
            tbl = union_tbl,
            map1_cls = __SHAPES_TO_COMPARE[uShp[0]],
            map2_cls = __SHAPES_TO_COMPARE[uShp[1]]
        ), db_api='psql').fcol.tolist()
        
        matrixTbl = q_to_ntbl(conPARAM, "{}_matrix".format(union_tbl), (
            "SELECT * FROM crosstab('"
                "SELECT CASE "
                    "WHEN foo.{map1_cls} IS NOT NULL "
                    "THEN foo.{map1_cls} ELSE jtbl.flyr "
                "END AS lulc1_cls, CASE "
                    "WHEN foo.{map2_cls} IS NOT NULL "
                    "THEN foo.{map2_cls} ELSE jtbl.slyr "
                "END AS lulc2_cls, CASE "
                    "WHEN foo.garea IS NOT NULL "
                    "THEN round(CAST(foo.garea / 1000000 AS numeric)"
                    ", 3) ELSE 0 "
                "END AS garea FROM ("
                    "SELECT CAST({map1_cls} AS text) AS {map1_cls}, "
                    "CAST({map2_cls} AS text) AS {map2_cls}, "
                    "SUM(ST_Area(geom)) AS garea "
                    "FROM {tbl} GROUP BY {map1_cls}, {map2_cls}"
                ") AS foo FULL JOIN ("
                    "SELECT f.flyr, s.slyr FROM ("
                        "SELECT CAST({map1_cls} AS text) AS flyr "
                        "FROM {tbl} GROUP BY {map1_cls}"
                    ") AS f, ("
                        "SELECT CAST({map2_cls} AS text) AS slyr "
                        "FROM {tbl} GROUP BY {map2_cls}"
                    ") AS s"
                ") AS jtbl "
                "ON foo.{map1_cls} = jtbl.flyr AND "
                "foo.{map2_cls} = jtbl.slyr "
                "ORDER BY 1,2"
            "') AS ct("
                "lulc_cls text, {crossCols}"
            ")"
        ).format(
            crossCols = ", ".join([
                "cls_{} numeric".format(c) for c in lulcCls]),
            tbl = union_tbl,
            map1_cls = __SHAPES_TO_COMPARE[uShp[0]],
            map2_cls = __SHAPES_TO_COMPARE[uShp[1]]
        ), api='psql')
        
        SYNTH_TBL[uShp] = {"TOTAL" : areaMapTbl, "MATRIX" : matrixTbl}
    
    # UNION ALL TOTAL TABLES
    total_table = tbls_to_tbl(
        conPARAM, [SYNTH_TBL[k]["TOTAL"] for k in SYNTH_TBL], 'total_table'
    )
    
    # Create table with % of agreement between each pair of maps
    mapsNames = query_to_df(conPARAM, (
        "SELECT lulc FROM ("
            "SELECT lulc_1 AS lulc FROM {tbl} GROUP BY lulc_1 "
            "UNION ALL "
            "SELECT lulc_2 AS lulc FROM {tbl} GROUP BY lulc_2"
        ") AS lu GROUP BY lulc ORDER BY lulc"
    ).format(tbl=total_table), db_api='psql').lulc.tolist()
    
    FLDS_TO_PIVOT = ["agree_percentage", "total_area"]
    
    Q = (
        "SELECT * FROM crosstab('"
            "SELECT CASE "
                "WHEN foo.lulc_1 IS NOT NULL THEN foo.lulc_1 ELSE jtbl.tmp1 "
            "END AS lulc_1, CASE "
                "WHEN foo.lulc_2 IS NOT NULL THEN foo.lulc_2 ELSE jtbl.tmp2 "
            "END AS lulc_2, CASE "
                "WHEN foo.{valCol} IS NOT NULL THEN foo.{valCol} ELSE 0 "
            "END AS agree_percentage FROM ("
                "SELECT lulc_1, lulc_2, {valCol} FROM {tbl} UNION ALL "
                "SELECT lulc_1, lulc_2, {valCol} FROM ("
                    "SELECT lulc_1 AS lulc_2, lulc_2 AS lulc_1, {valCol} "
                    "FROM {tbl}"
                ") AS tst"
            ") AS foo FULL JOIN ("
                "SELECT lulc_1 AS tmp1, lulc_2 AS tmp2 FROM ("
                    "SELECT lulc_1 AS lulc_1 FROM {tbl} GROUP BY lulc_1 "
                    "UNION ALL "
                    "SELECT lulc_2 AS lulc_1 FROM {tbl} GROUP BY lulc_2"
                ") AS tst_1, ("
                    "SELECT lulc_1 AS lulc_2 FROM {tbl} GROUP BY lulc_1 "
                    "UNION ALL "
                    "SELECT lulc_2 AS lulc_2 FROM {tbl} GROUP BY lulc_2"
                ") AS tst_2 WHERE lulc_1 = lulc_2 GROUP BY lulc_1, lulc_2"
            ") AS jtbl ON foo.lulc_1 = jtbl.tmp1 AND foo.lulc_2 = jtbl.tmp2 "
            "ORDER BY lulc_1, lulc_2"
        "') AS ct("
            "lulc_map text, {crossCols}"
        ")"
    )
    
    TOTAL_AGREE_TABLE = None
    TOTAL_AREA_TABLE  = None
    for f in FLDS_TO_PIVOT:
        if not TOTAL_AGREE_TABLE:
            TOTAL_AGREE_TABLE = q_to_ntbl(
                conPARAM, "agreement_table", Q.format(
                    tbl = total_table, valCol=f,
                    crossCols = ", ".join([
                        "{} numeric".format(map_) for map_ in mapsNames])
                ), api='psql'
            )
        
        else:
            TOTAL_AREA_TABLE = q_to_ntbl(
                conPARAM, "area_table", Q.format(
                    tbl = total_table, valCol=f,
                    crossCols = ", ".join([
                        "{} numeric".format(map_) for map_ in mapsNames])
                ), api='psql'
            )
    
    # Union Mapping
    UNION_MAPPING = pandas.DataFrame([[
        get_filename(k[0]), get_filename(k[1]),
        get_filename(UNION_SHAPE[k])] for k in UNION_SHAPE],
        columns=['shp_a', 'shp_b', 'union_shp']
    ) if GIS_SOFTWARE == "ARCGIS" else pandas.DataFrame([[
        k[0], k[1], get_filename(UNION_SHAPE[k])] for k in UNION_SHAPE],
        columns=['shp_a', 'shp_b', 'union_shp']
    )
    
    UNION_MAPPING = df_to_db(conPARAM, UNION_MAPPING, 'union_map', api='psql')
    
    # Export Results
    TABLES = [UNION_MAPPING, TOTAL_AGREE_TABLE, TOTAL_AREA_TABLE] + [
        SYNTH_TBL[x]["MATRIX"] for x in SYNTH_TBL
    ]
    
    SHEETS = ["union_map", "agreement_percentage", "area_with_data_km"] + [
        "{}_{}".format(
            get_filename(x[0])[:15], get_filename(x[1])[:15]
        ) for x in SYNTH_TBL
    ]
    
    db_to_xls(
        conPARAM, ["SELECT * FROM {}".format(x) for x in TABLES],
        REPORT, sheetsNames=SHEETS, dbAPI='psql'
    )
    
    return REPORT

