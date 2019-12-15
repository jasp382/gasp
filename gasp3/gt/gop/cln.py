"""
Clean Geometries
"""

def remove_deadend(inShp, outShp, con_db=None):
    """
    Remove deadend
    """
    
    from gasp3.pyt.oss     import get_filename
    from gasp3.sql.mng.db  import create_db
    from gasp3.sql.to      import shp_to_psql
    from gasp3.sql.gop.cln import rm_deadend
    from gasp3.gt.to.shp   import dbtbl_to_shp
    
    conDB = {
        "HOST" : 'localhost', 'PORT' : '5432', 'USER' : 'postgres',
        'PASSWORD' : 'admin', 'TEMPLATE' : 'postgis_template'
    } if not con_db else con_db
    
    # Create DB
    if "DATABASE" not in conDB:
        conDB["DATABASE"] = create_db(conDB, get_filename(
            inShp, forceLower=True
        ), api='psql')
    
    else:
        from gasp3.sql.i import db_exists
        isDb = db_exists(conDB, conDB["DATABASE"])
        
        if not isDb:
            conDB["DB"] = conDB["DATABASE"]
            del conDB["DATABASE"]
            
            conDB["DATABASE"] = create_db(conDB, conDB["DB"])
    
    # Send data to Database
    inTbl = shp_to_psql(conDB, inShp, api="shp2pgsql", encoding="LATIN1")
    
    # Produce result
    out_tbl = rm_deadend(conDB, inTbl, get_filename(
        outShp, forceLower=True))
    
    # Export result
    outshp = dbtbl_to_shp(
        conDB, out_tbl, "geom", outShp, inDB='psql', tableIsQuery=None,
        api="pgsql2shp"
    )
    
    return outShp

