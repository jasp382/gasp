"""
Tools for process geographic data on PostGIS
"""


def st_near(link, inTbl, inTblPK, inGeom, nearTbl, nearGeom, output,
            near_col='near', untilDist=None, colsInTbl=None, colsNearTbl=None):
    """
    Near tool for PostGIS
    """
    
    from gasp.pyt    import obj_to_lst
    from gasp.sql.to import q_to_ntbl
    
    _out = q_to_ntbl(link, output, (
        "SELECT DISTINCT ON (s.{colPk}) "
        "{inTblCols}, {nearTblCols}"
        "ST_Distance("
            "s.{ingeomCol}, h.{negeomCol}"
        ") AS {nearCol} FROM {in_tbl} AS s "
        "LEFT JOIN {near_tbl} AS h "
        "ON ST_DWithin(s.{ingeomCol}, h.{negeomCol}, {dist_v}) "
        "ORDER BY s.{colPk}, ST_Distance(s.{ingeomCol}, h.{negeomCol})"
    ).format(
        colPk=inTblPK,
        inTblCols="s.*" if not colsInTbl else ", ".join([
            "s.{}".format(x) for x in obj_to_lst(colsInTbl)
        ]),
        nearTblCols="" if not colsNearTbl else ", ".join([
            "h.{}".format(x) for x in obj_to_lst(colsNearTbl)
        ]) + ", ",
        ingeomCol=inGeom, negeomCol=nearGeom,
        nearCol=near_col, in_tbl=inTbl, near_tbl=nearTbl,
        dist_v="100000" if not untilDist else untilDist
    ), api='psql')
    
    
    return output


def st_near2(link, inTbl, inGeom, nearTbl, nearGeom, output,
            near_col='near'):
    """
    Near tool for PostGIS
    """
    
    from gasp.pyt    import obj_to_lst
    from gasp.sql.to import q_to_ntbl
    
    _out = q_to_ntbl(link, output, (
        "SELECT m.*, ST_Distance(m.{ingeom}, j.geom) AS {distCol} "
        "FROM {t} AS m, ("
            "SELECT ST_UnaryUnion(ST_Collect({neargeom})) AS geom "
            "FROM {tblNear}"
        ") AS j"
    ).format(
        ingeom=inGeom, distCol=near_col, t=inTbl, neargeom=nearGeom,
        tblNear=nearTbl
    ), api='psql')
    
    
    return output


def splite_near(sqdb, tbl, nearTbl, tblGeom, nearGeom, output, whrNear=None,
            outIsFile=None):
    """
    Near Analysis using Spatialite
    """
    
    Q = (
        "SELECT m.*, ST_Distance(m.{inGeom}, j.geom) AS dist_near "
        "FROM {t} AS m, ("
            "SELECT ST_UnaryUnion(ST_Collect({neargeom})) AS geom "
            "FROM {tblNear}{nearwhr}"
        ") AS j"
    ).format(
        inGeom=tblGeom, t=tbl, neargeom=nearGeom, tblNear=nearTbl,
        nearwhr="" if not whrNear else " WHERE {}".format(whrNear)
    )
    
    if outIsFile:
        from gasp.gt.attr import sel_by_attr
        
        sel_by_attr(sqdb, Q, output, api_gis='ogr')
    
    else:
        from gasp.sql.to import q_to_ntbl
        
        q_to_ntbl(sqdb, output, Q, api='ogr2ogr')
    
    return output


def st_buffer(conParam, inTbl, bfDist, geomCol, outTbl, bufferField="geometry",
              whrClause=None, dissolve=None, cols_select=None, outTblIsFile=None):
    """
    Using Buffer on PostGIS Data
    """
    
    from gasp.pyt import obj_to_lst
    
    dissolve = obj_to_lst(dissolve) if dissolve != "ALL" else "ALL"
    
    SEL_COLS = "" if not cols_select else ", ".join(obj_to_lst(cols_select))
    DISS_COLS = "" if not dissolve or dissolve == "ALL" else ", ".join(dissolve)
    GRP_BY = "" if not dissolve else "{}, {}".format(SEL_COLS, DISS_COLS) if \
        SEL_COLS != "" and DISS_COLS != "" else SEL_COLS \
        if SEL_COLS != "" else DISS_COLS if DISS_COLS != "" else ""
    
    Q = (
        "SELECT{sel}{spFunc}{geom}, {_dist}{endFunc} AS {bf} "
        "FROM {t}{whr}{grpBy}"
    ).format(
        sel = " " if not cols_select else " {}, ".format(SEL_COLS),
        spFunc="ST_Buffer(" if not dissolve else \
            "ST_UnaryUnion(ST_Collect(ST_Buffer(",
        geom=geomCol, _dist=bfDist,
        endFunc=")" if not dissolve else ")))",
        t=inTbl,
        grpBy=" GROUP BY {}".format(GRP_BY) if GRP_BY != "" else "",
        whr="" if not whrClause else " WHERE {}".format(whrClause),
        bf=bufferField
    )
    
    if not outTblIsFile:
        from gasp.sql.to import q_to_ntbl
        
        outTbl = q_to_ntbl(conParam, outTbl, Q, api='psql')
    else:
        from gasp.gt.toshp.db import dbtbl_to_shp
        
        dbtbl_to_shp(conParam, Q, bufferField, outTbl, api='pgsql2shp',
            tableIsQuery=True
        )
    
    return outTbl

def splite_buffer(db, table, dist, geomField, outTbl,
              cols_select=None, bufferField="geometry",
              whrClause=None, outTblIsFile=None, dissolve=None):
    """
    Run ST_Buffer
    
    if not dissolve, no generalization will be applied; 
    if dissolve == to str or list, a generalization will be accomplish
    using the fields referenced by this object;
    if dissolve == 'ALL', all features will be dissolved.
    """
    
    from gasp.pyt import obj_to_lst
    
    dissolve = obj_to_lst(dissolve) if dissolve != "ALL" else "ALL"
    
    sql = (
        "SELECT{sel}{spFunc}{geom}, {_dist}{endFunc} AS {bf} "
        "FROM {tbl}{whr}{grpBy}"
    ).format(
        sel = " " if not cols_select else " {}, ".format(
            ", ".join(obj_to_lst(cols_select))
        ),
        tbl=table,
        geom=geomField, _dist=str(dist), bf=bufferField,
        whr="" if not whrClause else " WHERE {}".format(whrClause),
        spFunc="ST_Buffer(" if not dissolve else \
            "ST_UnaryUnion(ST_Collect(ST_Buffer(",
        endFunc = ")" if not dissolve else ")))",
        grpBy="" if not dissolve or dissolve == "ALL" else " GROUP BY {}".format(
            ", ".join(dissolve)
        )
    )
    
    if outTblIsFile:
        from gasp.gt.attr import sel_by_attr
        
        sel_by_attr(db, sql, outTbl, api_gis='ogr')
    
    else:
        from gasp.sql.to import q_to_ntbl
        
        q_to_ntbl(db, outTbl, sql, api='ogr2ogr')
    
    return outTbl

