"""
Geometry management
"""

def fix_geom(conParam, table, geom, out_tbl, colsSelect=None, whr=None):
    """
    Remove some topological incorrections on the PostGIS data
    """
    
    from gasp.sql.to import q_to_ntbl
    
    if not colsSelect:
        from gasp.sql.i import cols_name
        
        cols_tbl = ['{}.{}'.format(
            table, x) for x in cols_name(
                conParam, table, sanitizeSpecialWords=None
            ) if x != geom
        ]
    else:
        from gasp.pyt import obj_to_lst
        
        cols_tbl = ['{}.{}'.format(
            table, x) for x in obj_to_lst(colsSelect) if x != geom
        ]
    
    Q = "SELECT {c}, ST_MakeValid({g}) AS {g} FROM {t}{w}".format(
        c=", ".join(cols_tbl), g=geom, t=table,
        w="" if not whr else " WHERE {}".format(whr)
    )
    
    ntbl = q_to_ntbl(conParam, out_tbl, Q, api='psql')
    
    return ntbl


def xycols_to_geom(conP, intable, x_col, y_col, outtable,
                   geom_field='geom', epsg=4326):
    """
    X and Y Colums to PostGIS Geom Column
    """
    
    from gasp.sql.to import q_to_ntbl
    
    return q_to_ntbl(conP, outtable, (
        "SELECT *, ST_SetSRID(ST_MakePoint({}, {}), {}) AS {} "
        "FROM {}"
    ).format(
        x_col, y_col, str(epsg), geom_field, intable
    ), api='psql')


def geom_to_points(conParam, table, geomCol, outTable,
                   selCols=None, newGeomCol=None):
    """
    Convert a Polygon/Polyline Geometry to Points
    
    Equivalent to feature to point tool
    """
    
    from gasp.pyt    import obj_to_lst
    from gasp.sql.to import q_to_ntbl
    
    selCols = obj_to_lst(selCols)
    
    Q = (
        "SELECT {cols}(ST_DumpPoints({geom})).geom AS {newCol} "
        "FROM {tbl}"
    ).format(
        cols = "" if not selCols else "{}, ".format(", ".join(selCols)),
        geom=geomCol, newCol="geom" if not newGeomCol else newGeomCol,
        tbl=table
    )
    
    return q_to_ntbl(conParam, outTable, Q, api='psql')


def add_endpoints_to_table(conP, inTable, outTable, 
                           idCol='gid', geomCol='geom',
                           startCol="start_vertex",
                           endCol="end_vertex"):
    """
    Add start/end points columns to table
    """
    
    from gasp.sql.to import q_to_ntbl
    from gasp.sql.i  import cols_name
    
    return q_to_ntbl(conP, outTable, (
        "SELECT {cols}, {stPnt}, {endPnt} FROM ("
            "SELECT *, lead({stPnt}) OVER ("
                "PARTITION BY {colId} ORDER BY pnt_idx) AS {endPnt} "
            "FROM ("
                "SELECT {cols}, pnt_idx, {stPnt}, "
                "CASE "
                    "WHEN pnt_idx = 1 OR pnt_idx = MAX(pnt_idx) "
                        "OVER (PARTITION BY {colId}) "
                    "THEN 1 ELSE 0 END AS pnt_cat "
                "FROM ("
                    "SELECT {cols}, "
                    "(ST_DumpPoints({geomF})).path[1] AS pnt_idx, "
                    "(ST_DumpPoints({geomF})).geom AS {stPnt} "
                    "FROM {table}"
                ") AS foo"
            ") AS foo2 "
            "WHERE pnt_cat = 1"
        ") AS foo3 "
        "WHERE {endPnt} IS NOT NULL "
        "ORDER BY {colId}, pnt_idx"
    ).format(
        cols  =", ".join(cols_name(conP, inTable)),
        stPnt = startCol, endPnt = endCol, colId = idCol,
        geomF = geomCol , table  = inTable
    ), api='psql')


def check_endpoint_ispoint(conParam, lnhTable, pntTable, outTable,
                           nodeStart, nodeEnd, pointId, pntGeom="geom"):
    """
    Check if a Start/End point in a table with line geometries is a point 
    in other table.
    """
    
    from gasp.sql.to import q_to_ntbl
    from gasp.sql.i  import cols_name
    
    tCols = [x for x in cols_name(
        conParam, lnhTable) if x != nodeStart and x != nodeEnd
    ]
    
    return q_to_ntbl(conParam, outTable, (
        "SELECT * FROM ("
            "SELECT {fooCols}, foo.{stPnt}, foo.{endPnt}, "
            "CASE "
                "WHEN start_tbl.start_x IS NOT NULL THEN 1 ELSE 0 "
            "END AS start_isstop, "
            "CASE "
                "WHEN end_tbl.end_x IS NOT NULL THEN 1 ELSE 0 "
            "END AS end_isstop, start_tbl.start_id, end_tbl.end_id "
            "FROM ("
                "SELECT *, "
                "CAST(((round(CAST(ST_X({stPnt}) AS numeric), 4)) * 10000) "
                    "AS integer) AS start_x, "
                "CAST(((round(CAST(ST_Y({stPnt}) AS numeric), 4)) * 10000) "
                    "AS integer) AS start_y, "
                "CAST(((round(CAST(ST_X({endPnt}) AS numeric), 4)) * 10000) "
                    "AS integer) AS end_x, "
                "CAST(((round(CAST(ST_Y({endPnt}) AS numeric), 4)) * 10000) "
                    "AS integer) AS end_y "
                "FROM {lnhT}"
            ") AS foo "
            "LEFT JOIN ("
                "SELECT CAST(((round(CAST(ST_X({pntG}) AS numeric), 4)) "
                    "* 10000) AS integer) AS start_x, "
                "CAST(((round(CAST(ST_Y({pntG}) AS numeric), 4)) "
                    "* 10000) AS integer) AS start_y, "
                "{pntid} AS start_id FROM {pntT}"
            ") AS start_tbl "
            "ON foo.start_x = start_tbl.start_x AND "
            "foo.start_y = start_tbl.start_y "
            "LEFT JOIN ("
                "SELECT CAST(((round(CAST(ST_X({pntG}) AS numeric), 4)) "
                    "* 10000) AS integer) AS end_x, "
                "CAST(((round(CAST(ST_Y({pntG}) AS numeric), 4)) "
                    "* 10000) as integer) AS end_y, "
                "{pntid} AS end_id FROM {pntT}"
            ") AS end_tbl "
            "ON foo.end_x = end_tbl.end_x AND foo.end_y = end_tbl.end_y"
        ") AS foo2 "
        "GROUP BY {cols}, {stPnt}, {endPnt}, start_isstop, end_isstop, "
        "start_id, end_id"
    ).format(
        fooCols = ", ".join(["foo.{}".format(c) for c in tCols]),
        stPnt = nodeStart, endPnt = nodeEnd, lnhT = lnhTable,
        pntT = pntTable, pntG = pntGeom,
        cols = ", ".join(tCols), pntid=pointId
    ), api='psql')


def pnts_to_lines(conParam, inTable, outTable, entityCol, orderCol,
                  geomCol=None, xCol=None, yCol=None, epsg=4326):
    """
    Given a table with points by entity, create a new table with a polyline
    for each entity. The points are added to the polyline based on a 
    sequence in one column.
    """
    
    if not geomCol:
        if not xCol or not yCol:
            raise ValueError(
                'If geomCol is not specified, xCol and ycol must replace it!')
    
    from gasp.sql.to import q_to_ntbl
    
    geomRef = geomCol if geomCol else "ST_MakePoint({}, {})".format(xCol, yXol)
    
    Q = (
        "SELECT {entCol}, ST_SetSRID(ST_MakeLine("
            "array_agg({pntCol} ORDER BY {orderF})), {srs}) "
        "FROM {tbl} GROUP BY {entCol}"
    ).format(
        entCol=entityCol, pntCol=geomRef, orderF=orderCol,
        srs=epsg, tbl=inTable
    )
    
    return q_to_ntbl(conParam, outTable, Q, api='psql')


def check_geomtype_in_table(conParam, table, geomCol='geom'):
    """
    Return the number of geometry types in table
    """
    
    from gasp.sql.fm import q_to_obj
    
    return int(q_to_obj(conParam, (
        "SELECT COUNT(*) AS row_count FROM ("
            "SELECT ST_GeometryType((ST_Dump({})).geom) AS cnt_geom "
            "FROM {} GROUP BY ST_GeometryType((ST_Dump({})).geom)"
        ") AS foo"
    ).format(geomCol, table, geomCol), db_api='psql').iloc[0].row_count)


def select_main_geom_type(conparam, table, outbl, geomCol='geom'):
    """
    Assuming a table with several geometry types, this method
    counts the rows for each geometry type and select the rows with a geometry
    type with more rows
    """
    
    from gasp.sql.to import q_to_ntbl
    from gasp.sql.i  import cols_name
    
    COLS = [x for x in cols_name(
        conparam, table, sanitizeSpecialWords=None
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
    
    return q_to_ntbl(conparam, outbl, Q, api='psql')


def add_idx_to_geom(conParam, table, geomCol):
    """
    Add index to Geometry
    """
    
    from gasp.sql.c import sqlcon
    
    con = sqlcon(conParam)
    cursor = con.cursor()
    
    cursor.execute("CREATE INDEX {tbl}_{col}_idx ON {tbl} USING gist ({col})".format(
        tbl=table, col=geomCol
    ))
    
    con.commit()
    
    cursor.close()
    con.close()
    
    return table

