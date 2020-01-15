"""
Geometric Conversion using SQL
"""

def lnh_to_polg(con_db, intbl, outtbl):
    """
    Line to Polygons
    """
    
    from gasp.sql.mng.tbl import q_to_ntbl
    
    Q = (
        "SELECT ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS gid, "
        "(ST_Dump(ST_Polygonize(geom))).geom AS geom FROM ("
            "SELECT ST_Node(ST_Collect(geom)) AS geom FROM ("
                "SELECT (ST_Dump(geom)).geom FROM {}"
            ") AS foo"
        ") AS foo"
    ).format(intbl)
    
    return q_to_ntbl(con_db, outtbl, Q)
