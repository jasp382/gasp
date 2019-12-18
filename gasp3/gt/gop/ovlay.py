"""
Overlay operations
"""


"""
Intersection in the same Feature Class/Table
"""

def line_intersect_to_pnt(conDB, inShp, outShp):
    """
    Get Points where two line features of the same feature class
    intersects.
    """
    
    from gasp3.pyt.oss       import get_filename
    from gasp3.gt.to.shp     import dbtbl_to_shp
    from gasp3.sql.mng.db    import create_db
    from gasp3.sql.to        import shp_to_psql
    from gasp3.sql.gop.ovlay import line_intersection_pnt
    
    # Create DB if necessary
    if "DATABASE" not in conDB:
        conDB["DATABASE"] = create_db(conDB, get_filename(
            inShp, forceLower=True
        ))
    
    else:
        from gasp3.sql.i import db_exists
        
        isDb = db_exists(conDB, conDB["DATABASE"])
        
        if not isDb:
            conDB["DB"] = conDB["DATABASE"]
            del conDB["DATABASE"]
            conDB["DATABASE"] = create_db(conDB, conDB["DB"])
    
    # Send data to DB
    inTbl = shp_to_psql(conDB, inShp, api="shp2pgsql")
    
    # Get result
    outTbl = line_intersection_pnt(conDB, inTbl, get_filename(
        outShp, forceLower=True))
    
    # Export data from DB
    outShp = dbtbl_to_shp(
        conDB, outTbl, "geom", outShp, inDB='psql',
        tableIsQuery=None, api="pgsql2shp")
    
    return outShp

