"""
Clean Geometries
"""

def remove_deadend(inShp, outShp, con_db=None):
    """
    Remove deadend
    """
    
    from gasp.pyt.oss     import get_filename
    from gasp.sql.db      import create_db
    from gasp.sql.to      import shp_to_psql
    from gasp.sql.gop.cln import rm_deadend
    from gasp.gt.to.shp   import dbtbl_to_shp
    
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
        from gasp.sql.i import db_exists
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

