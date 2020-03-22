"""
Geometric Properties
"""

def tbl_ext(db, table, geomCol):
    """
    Return extent of the geometries in one pgtable
    """
    
    from gasp.sql.fm import q_to_obj
    
    q = (
        "SELECT MIN(ST_X(pnt_geom)) AS eleft, MAX(ST_X(pnt_geom)) AS eright, "
        "MIN(ST_Y(pnt_geom)) AS bottom, MAX(ST_Y(pnt_geom)) AS top "
        "FROM ("
            "SELECT (ST_DumpPoints({geomcol})).geom AS pnt_geom "
            "FROM {tbl}"
        ") AS foo"
    ).format(tbl=table, geomcol=geomCol)
    
    ext = q_to_obj(db, q, db_api='psql').to_dict(orient='index')[0]
    
    return [
        ext['eleft'], ext['bottom'], ext['eright'], ext['top']
    ]


def tbl_geomtype(db, table, geomCol='geom'):
    """
    Return the number of geometry types in table
    """
    
    from gasp.sql.fm import q_to_obj
    
    return int(q_to_obj(db, (
        "SELECT COUNT(*) AS row_count FROM ("
            "SELECT ST_GeometryType((ST_Dump({})).geom) AS cnt_geom "
            "FROM {} GROUP BY ST_GeometryType((ST_Dump({})).geom)"
        ") AS foo"
    ).format(geomCol, table, geomCol), db_api='psql').iloc[0].row_count)


def select_main_geom_type(db, table, outbl, geomCol='geom'):
    """
    Assuming a table with several geometry types, this method
    counts the rows for each geometry type and select the rows with a geometry
    type with more rows
    """
    
    from gasp.sql.to import q_to_ntbl
    from gasp.sql.i  import cols_name
    
    COLS = [x for x in cols_name(
        db, table, sanitizeSpecialWords=None
    ) if x != geomCol]
    
    Q = (
        "SELECT {cols}, {geomcol} FROM ("
            "SELECT *, MAX(jtbl.geom_cont) OVER (PARTITION BY "
            "jtbl.tst) AS max_cnt FROM ("
                "SELECT {cols}, (ST_Dump({geomcol})).geom AS {geomcol}, "
                "ST_GeometryType((ST_Dump({geomcol})).geom) AS geom_type "
                "FROM {tbl}"
            ") AS foo INNER JOIN ("
                "SELECT ST_GeometryType((ST_Dump({geomcol})).geom) AS gt, "
                "COUNT(ST_GeometryType((ST_Dump({geomcol})).geom)) AS geom_cont, "
                "1 AS tst FROM {tbl} GROUP BY ST_GeometryType((ST_Dump({geomcol})).geom)"
            ") AS jtbl ON foo.geom_type = jtbl.gt"
        ") AS foo WHERE geom_cont = max_cnt"
    ).format(
        cols=", ".join(COLS), geomcol=geomCol,
        tbl=table
    )
    
    return q_to_ntbl(db, outbl, Q, api='psql')
