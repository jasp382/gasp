"""
Geometry management
"""


def add_endpoints_to_table(db, inTable, outTable, 
                           idCol='gid', geomCol='geom',
                           startCol="start_vertex",
                           endCol="end_vertex"):
    """
    Add start/end points columns to table
    """
    
    from gasp.sql.to import q_to_ntbl
    from gasp.sql.i  import cols_name
    
    return q_to_ntbl(db, outTable, (
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
        cols  =", ".join(cols_name(db, inTable)),
        stPnt = startCol, endPnt = endCol, colId = idCol,
        geomF = geomCol , table  = inTable
    ), api='psql')


def check_endpoint_ispoint(db, lnhTable, pntTable, outTable,
                           nodeStart, nodeEnd, pointId, pntGeom="geom"):
    """
    Check if a Start/End point in a table with line geometries is a point 
    in other table.
    """
    
    from gasp.sql.to import q_to_ntbl
    from gasp.sql.i  import cols_name
    
    tCols = [x for x in cols_name(
        db, lnhTable) if x != nodeStart and x != nodeEnd
    ]
    
    return q_to_ntbl(db, outTable, (
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

