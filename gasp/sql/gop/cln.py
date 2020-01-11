"""
Clean Geometries
"""

def rm_deadend(con_db, in_tbl, out_tbl):
    """
    Remove deadend
    """
    
    from gasp.sql.i       import cols_name, row_num
    from gasp.sql.mng.tbl import q_to_ntbl
    from gasp.sql.mng.tbl import rename_tbl
    
    # Sanitize In table
    cols = ", ".join([c for c in cols_name(
        con_db, in_tbl, sanitizeSpecialWords=True, api='psql'
    ) if c != 'geom' and c != 'gid'])
    
    _t = q_to_ntbl(con_db, "san_geom", (
        "SELECT gid, {cln}, geom, "
        "ST_AsText(ST_StartPoint(geom)) AS pnt_start, "
        "ST_AsText(ST_EndPoint(geom)) AS pnt_end FROM ("
            "SELECT gid, {cln}, (ST_Dump(geom)).geom AS geom "
            "FROM {t}"
        ") AS foo"
    ).format(cln=cols, t=in_tbl))
    
    run_=1
    i = 1
    while run_:
        # Get Table with Points of lines to delete
        delpnt = q_to_ntbl(con_db, "del_pnt_{}".format(str(i)), (
            "SELECT ROW_NUMBER() OVER (ORDER BY txtgeom) AS idx, "
            "txtgeom FROM ("
                "SELECT txtgeom, COUNT(txtgeom) AS npnt FROM ("
                    "SELECT pnt_start AS txtgeom "
                    "FROM {t} UNION ALL "
                    "SELECT pnt_end AS txtgeom "
                    "FROM {t}"
                ") AS tbl GROUP BY txtgeom"
            ") AS delg WHERE npnt=1"
        ).format(t=_t))
        
        npnt = row_num(con_db, delpnt, api='psql')
        
        if not npnt:
            run_ = None
            break
        
        # Get Lines without dead-end
        Q = (
            "SELECT mtbl.* "
            "FROM {mtbl} AS mtbl LEFT JOIN {ptbl} AS st_tbl "
            "ON mtbl.pnt_start = st_tbl.txtgeom "
            "LEFT JOIN {ptbl} AS end_tbl "
            "ON mtbl.pnt_end = end_tbl.txtgeom "
            "WHERE st_tbl.txtgeom IS NULL AND "
            "end_tbl.txtgeom IS NULL"
        ).format(cls=cols, mtbl=_t, ptbl=delpnt)
        
        _t = q_to_ntbl(con_db, "rows_{}".format(str(i)), Q)
        
        i += 1
    
    rename_tbl(con_db, {_t : out_tbl})
    
    return out_tbl

