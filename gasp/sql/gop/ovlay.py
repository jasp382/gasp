"""
Overlay operations
"""

"""
Intersection in the same Feature Class/Table
"""

def line_intersection_pnt(conDB, inTbl, outTbl):
    """
    Get Points where two line features of the same feature class
    intersects.
    """
    
    from gasp.sql.mng.tbl import q_to_ntbl
    
    # Get Points representing intersection
    Q_a = (
        "SELECT foo.gid, "
        "ST_Intersection(foo.geom, foo2.tstgeom) AS geom "
        "FROM (SELECT gid, geom FROM {t}) AS foo, ("
            "SELECT gid AS tstfid, geom AS tstgeom "
            "FROM {t}"
        ") AS foo2 "
        "WHERE foo.gid <> foo2.tstfid AND "
        "ST_Intersects(foo.geom, foo2.tstgeom)"
    ).format(t=inTbl)
    
    Q_b = (
        "SELECT gid AS ogid, (ST_Dump(geom)).geom AS geom FROM ("
            "SELECT gid, "
            "CASE "
                "WHEN ST_GeometryType(geom) = 'ST_LineString' "
                "THEN ST_Collect(ST_StartPoint(geom), ST_EndPoint(geom)) "
                "ELSE geom "
            "END AS geom FROM ("
                "SELECT gid, (ST_Dump(geom)).geom AS geom "
                "FROM ({t}) AS ttbl"
            ") AS tbl"
        ") AS tbll"
    ).format(t=Q_a)
    
    allpnt = q_to_ntbl(conDB, "all_pnt", Q_b)
    
    Q_main = (
        "SELECT ogid, (ogid - 1) AS ofid, geom FROM ("
            "SELECT mtbl.*, st_tbl.st_pnt, st_tbl.end_pnt, "
            "CASE "
                "WHEN mtbl.geom = st_tbl.st_pnt "
                "THEN 1 ELSE 0 "
            "END AS is_start, "
            "CASE "
                "WHEN mtbl.geom = st_tbl.end_pnt "
                "THEN 1 ELSE 0 "
            "END AS is_end "
            "FROM {bpnt} AS mtbl INNER JOIN ("
                "SELECT gid, ST_StartPoint(geom) AS st_pnt, "
                "ST_EndPoint(geom) AS end_pnt FROM ("
                    "SELECT gid, (ST_Dump(geom)).geom AS geom "
                    "FROM {t}"
                ") AS foo"
            ") AS st_tbl "
            "ON mtbl.ogid = st_tbl.gid"
        ") AS foo WHERE is_start = 0 AND is_end = 0"
    ).format(bpnt=allpnt, t=inTbl)
    
    return q_to_ntbl(conDB, outTbl, Q_main)

