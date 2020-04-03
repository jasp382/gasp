"""
OSM to DB
"""

def osm_to_psql(osmXml, osmdb):
    """
    Use GDAL to import osmfile into PostGIS database
    """
    
    from gasp           import exec_cmd
    from gasp.cons.psql import con_psql
    from gasp.sql.i     import db_exists

    is_db = db_exists(osmdb)

    if not is_db:
        from gasp.sql.db import create_db

        create_db(osmdb, api='psql')

    con = con_psql()
    
    cmd = (
        "ogr2ogr -f PostgreSQL \"PG:dbname='{}' host='{}' port='{}' "
        "user='{}' password='{}'\" {} -lco COLUM_TYPES=other_tags=hstore"
    ).format(
        osmdb, con["HOST"], con["PORT"],
        con["USER"], con["PASSWORD"], osmXml
    )
    
    cmdout = exec_cmd(cmd)
    
    return osmdb


def osm_to_relationaldb(osmData, inSchema, osmGeoTbl, osmCatTbl, osmRelTbl,
                        outSQL=None, db_name=None):
    """
    PostgreSQL - OSM Data to Relational Model
    
    TODO: Just work for one geom table at once
    
    E.g.
    osmData = '/home/jasp/flainar/osm_centro.xml'
    
    inSchema = {
        "TBL" : 'points', 'FID' : 'CAST(osm_id AS bigint)',
        "COLS" : [
            'name',
            "ST_X(wkb_geometry) AS longitude",
            "ST_Y(wkb_geometry) AS latitude",
            "wkb_geometry AS geom",
            "NULL AS featurecategoryid",
            "NULL AS flainarcategoryid",
            "NULL AS createdby",
            "NOW() AS createdon",
            "NULL AS updatedon",
            "NULL AS deletedon"
        ],
        "NOT_KEYS" : [
            'ogc_fid', 'osm_id', 'name', "wkb_geometry",
            'healthcare2', 'other_tags'
        ]
    }
    
    osmGeoTbl = {"TBL" : 'position', "FID" : 'positionid'}
    
    osmCatTbl = {
        "TBL" : 'osmcategory', "FID" : "osmcategoryid",
        "KEY_COL" : "keycategory", "VAL_COL" : "value",
        "COLS" : [
            "NULL AS createdby", "NOW() AS createdon",
            "NULL AS updatedon", "NULL AS deletedon"
        ]
    }
    
    osmRelTbl = {
        "TBL" : "position_osmcat", "FID" : 'pososmcatid'
    }
    """
    
    from gasp.pyt.oss import fprop
    from gasp.sql.i   import cols_name
    from gasp.sql.to  import q_to_ntbl
    from gasp.sql.db  import create_db
    
    # Create DB
    db = create_db(fprop(osmData, 'fn') if not db_name else db_name, api='psql')
    
    # Send OSM data to Database
    osm_to_psql(osmData, db)
    
    # Get KEYS COLUMNS
    cols = cols_name(db, inSchema["TBL"], sanitizeSpecialWords=None)
    transcols = [c for c in cols if c not in inSchema["NOT_KEYS"]]
    
    # Create osmGeoTbl 
    osmgeotbl = q_to_ntbl(db, osmGeoTbl['TBL'], (
        "SELECT {} AS {}, {} FROM {}"
    ).format(
        inSchema["FID"], osmGeoTbl["FID"],
        ", ".join(inSchema["COLS"]), inSchema["TBL"]
    ), api='psql')
    
    # Create OSM categories table
    qs = [(
        "SELECT '{keyV}' AS {keyC}, CAST({t}.{keyV} AS text) AS {valC} "
        "FROM {t} WHERE {t}.{keyV} IS NOT NULL "
        "GROUP BY {t}.{keyV}"
    ).format(
        keyV=c, t=inSchema["TBL"], keyC=osmCatTbl["KEY_COL"],
        valC=osmCatTbl["VAL_COL"]
    ) for c in transcols]
    
    osmcatbl = q_to_ntbl(db, osmCatTbl["TBL"], (
        "SELECT row_number() OVER(ORDER BY {keyC}) "
        "AS {osmcatid}, {keyC}, {valC}{ocols} "
        "FROM ({q}) AS foo"
    ).format(
        q=" UNION ALL ".join(qs), keyC=osmCatTbl["KEY_COL"],
        osmcatid=osmCatTbl["FID"], valC=osmCatTbl["VAL_COL"],
        ocols="" if "COLS" not in osmCatTbl else ", {}".format(
            ", ".join(osmCatTbl["COLS"])
        )
    ), api='psql')
    
    # Create relation table
    qs = [(
        "SELECT {fid}, '{keyV}' AS key, CAST({t}.{keyV} AS text) AS osmval "
        "FROM {t} WHERE {t}.{keyV} IS NOT NULL"
    ).format(
        fid=inSchema["FID"], keyV=c, t=inSchema["TBL"]
    ) for c in transcols]
    
    osmreltbl = q_to_ntbl(db, osmRelTbl["TBL"], (
        "SELECT foo.{fid}, catbl.{osmcatfid} "
        "FROM ({mtbl}) AS foo INNER JOIN {catTbl} AS catbl "
        "ON foo.key = catbl.keycategory AND foo.osmval = catbl.value"
    ).format(
        mtbl=" UNION ALL ".join(qs), fid=inSchema["FID"],
        catTbl=osmCatTbl["TBL"], osmcatfid=osmCatTbl["FID"]
    ), api='psql')
    
    if not outSQL:
        return osmgeotbl, osmcatbl, osmreltbl
    else:
        from gasp.sql.fm import dump_tbls
        
        return dump_tbls(db, [osmgeotbl, osmcatbl, osmreltbl], outSQL)
