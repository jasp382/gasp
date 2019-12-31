"""
Projections in SQL
"""

def sql_proj(condb, tbl, otbl, oepsg, cols=None, geomCol=None,
    newGeom=None, whr=None):
    """
    Reproject geometric layer to another spatial reference system (srs)
    """

    from gasp.pyt         import obj_to_lst
    from gasp.sql.mng.tbl import q_to_ntbl

    geomCol = 'geom' if not geomCol else geomCol
    newGeom = 'geom' if not newGeom else newGeom

    if not cols:
        from gasp.sql.i import cols_name

        cols = cols_name(condb, tbl)

        cols.remove(geomCol)
    
    else:
        cols = obj_to_lst(cols)

        if geomCol in cols and geomCol == newGeom:
            cols.remove(geomCol)
            cols.append('{c} AS old_{c}'.format(c=geomCol))

    Q = (
        "SELECT {}, ST_Transform({}, {}) AS {} "
        "FROM {}{}"
    ).format(
        ", ".join(cols), geomCol, str(oepsg), newGeom, tbl,
        "" if not whr else " WHERE {}".format(whr)
    )

    return q_to_ntbl(condb, otbl, Q, api='psql')

