"""
Break Operations
"""

def shply_break_lines_on_points(lineShp, pointShp, lineIdInPntShp, splitedShp):
    """
    Break lines on points location
    
    The points should be contained by the lines;
    The points table should have a column with the id of the
    line that contains the point.
    
    lineIDInPntShp is a reference to the FID of lineShp
    """
    
    from shapely.ops       import split
    from shapely.geometry  import Point, LineString
    from gasp3.fm          import tbl_to_obj
    from gasp3.df.mng      import col_list_val_to_row
    from gasp3.gt.prop.prj import get_epsg_shp
    from gasp3.gt.to.shp   import df_to_shp
    from gasp3.df.to       import dict_to_df
    
    srs_code = get_epsg_shp(lineShp)
    
    # Sanitize line geometry
    def fix_line(line, point):
        buff = point.buffer(0.0001)
        
        splitLine = split(line, buff)
        
        nline = LineString(
            list(splitLine[0].coords) + list(point.coords) +
            list(splitLine[-1].coords)
        )
        
        return nline
    
    pnts  = tbl_to_obj(pointShp)
    lines = tbl_to_obj(lineShp, fields='ALL', output='dict')
    
    # Split Rows
    def split_geom(row):
        # Get related line
        rel_line = lines[row[lineIdInPntShp]]
        
        if type(rel_line["GEOM"]) != list:
            line_geom = fix_line(rel_line["GEOM"], row.geometry)
            
            split_lines = split(line_geom, row.geometry)
            
            lines[row[lineIdInPntShp]]["GEOM"] = [l for l in split_lines]
        
        else:
            for i in range(len(rel_line["GEOM"])):
                if rel_line["GEOM"][i].distance(row.geometry) < 1e-8:
                    line_geom = fix_line(rel_line["GEOM"][i], row.geometry)
                    split_lines = split(line_geom, row.geometry)
                    split_lines = [l for l in split_lines]
                    
                    lines[row[lineIdInPntShp]]["GEOM"][i] = split_lines[0]
                    lines[row[lineIdInPntShp]]["GEOM"] += split_lines[1:]
                    
                    break
                
                else:
                    continue
        return row
    
    pnts = pnts.apply(lambda x: split_geom(x), axis=1)
    
    # Result to Dataframe
    linesDf = dict_to_df(lines)
    
    # Where GEOM is a List, create a new row for each element in list
    linesDf = col_list_val_to_row(
        linesDf, "GEOM", geomCol="GEOM", epsg=srs_code
    )
    
    # Save result
    return df_to_shp(linesDf, splitedShp)


"""
V.edit possibilities
"""
def vedit_break(inShp, pntBreakShp,
                geomType='point,line,boundary,centroid'):
    """
    Use tool break
    """
    
    import os
    from grass.pygrass.modules import Module
    
    # Iterate over pntBreakShp to get all coords
    if os.path.isfile(pntBreakShp):
        from gasp3.fm import points_to_list
        lstPnt = points_to_list(pntBreakShp)
    else:
        from grass.pygrass.vector import VectorTopo
        
        pnt = VectorTopo(pntBreakShp)
        pnt.open(mode='r')
        lstPnt = ["{},{}".format(str(p.x), str(p.y)) for p in pnt]
    
    # Run v.edit
    m = Module(
        "v.edit", map=inShp, type=geomType, tool="break",
        coords=lstPnt,
        overwrite=True, run_=False, quiet=True
    )
    
    m()


def v_break_at_points(workspace, loc, lineShp, pntShp, conParam, srs, out_correct,
            out_tocorrect):
    """
    Break lines at points - Based on GRASS GIS v.edit
    
    Use PostGIS to sanitize the result
    
    TODO: Confirm utility
    Problem: GRASS GIS always uses the first line to break.
    """
    
    import os
    from gasp3.sql.to      import shp_to_psql
    from gasp3.gt.to.shp   import dbtbl_to_shp
    from gasp3.gt.wenv.grs import run_grass
    from gasp3.pyt.oss     import get_filename
    from gasp3.sql.mng.db  import create_db
    from gasp3.sql.mng.tbl import q_to_ntbl
    
    tmpFiles = os.path.join(workspace, loc)
    
    gbase = run_grass(workspace, location=loc, srs=srs)
    
    import grass.script       as grass
    import grass.script.setup as gsetup
    
    gsetup.init(gbase, workspace, loc, 'PERMANENT')
    
    from gasp3.gt.to.shp import shp_to_grs, grs_to_shp
    
    grsLine = shp_to_grs(
        lineShp, get_filename(lineShp, forceLower=True)
    )
    
    vedit_break(grsLine, pntShp, geomType='line')
    
    LINES = grass_converter(
        grsLine, os.path.join(tmpFiles, grsLine + '_v1.shp'), 'line')
    
    # Sanitize output of v.edit.break using PostGIS
    create_db(conParam, conParam["DB"], overwrite=True)
    conParam["DATABASE"] = conParam["DB"]
    
    LINES_TABLE = shp_to_psql(
        conParam, LINES, srsEpsgCode=srs,
        pgTable=get_filename(LINES, forceLower=True), api="shp2pgsql"
    )
    
    # Delete old/original lines and stay only with the breaked one
    Q = (
        "SELECT {t}.*, foo.cat_count FROM {t} INNER JOIN ("
            "SELECT cat, COUNT(cat) AS cat_count, "
            "MAX(ST_Length(geom)) AS max_len "
            "FROM {t} GROUP BY cat"
        ") AS foo ON {t}.cat = foo.cat "
        "WHERE foo.cat_count = 1 OR foo.cat_count = 2 OR ("
            "foo.cat_count = 3 AND ST_Length({t}.geom) <= foo.max_len)"
    ).format(t=LINES_TABLE)
    
    CORR_LINES = q_to_ntbl(
        conParam, "{}_corrected".format(LINES_TABLE), Q, api='psql'
    )
    
    # TODO: Delete Rows that have exactly the same geometry
    
    # Highlight problems that the user must solve case by case
    Q = (
        "SELECT {t}.*, foo.cat_count FROM {t} INNER JOIN ("
            "SELECT cat, COUNT(cat) AS cat_count FROM {t} GROUP BY cat"
        ") AS foo ON {t}.cat = foo.cat "
        "WHERE foo.cat_count > 3"
    ).format(t=LINES_TABLE)
    
    ERROR_LINES = q_to_ntbl(
        conParam, "{}_not_corr".format(LINES_TABLE), Q, api='psql'
    )
    
    dbtbl_to_shp(
        conParam, CORR_LINES, "geom", out_correct,
        api="pgsql2shp"
    )
    
    dbtbl_to_shp(
        conParam, ERROR_LINES, "geom", out_tocorrect,
        api="pgsql2shp"
    )


def break_lines_on_points(lineShp, pntShp, outShp, lnhidonpnt,
                          api='shply', conDB=None):
    """
    Break lines on points location
    
    api's available:
    - shply (shapely);
    - psql (postgis);
    """
    
    if api == 'shply':
        result = shply_break_lines_on_points(
            lineShp, pntShp, lnhidonpnt, outShp)
    
    elif api == 'psql':
        from gasp3.pyt.oss     import get_filename
        from gasp3.sql.mng.db  import create_db
        from gasp3.sql.to      import shp_to_psql
        from gasp3.gt.to.shp   import dbtbl_to_shp
        from gasp3.sql.gop.brk import split_lines_on_pnt
        
        conDB = {
            "HOST" : 'localhost', 'PORT' : '5432', 'USER' : 'postgres',
            'PASSWORD' : 'admin', 'TEMPLATE' : 'postgis_template'
        } if not conDB else conDB
        
        # Create DB
        if "DATABASE" not in conDB:
            conDB["DATABASE"] = create_db(conDB, get_filename(
                lineShp, forceLower=True
            ))
        
        else:
            from gasp3.sql.i import db_exists
            isDb = db_exists(conDB, conDB["DATABASE"])
            
            if not isDb:
                conDB["DB"] = conDB["DATABASE"]
                del conDB["DATABASE"]
                
                conDB["DATABASE"] = create_db(conDB, conDB["DB"])
        
        # Send Data to BD
        lnhTbl = shp_to_psql(conDB, lineShp, api="shp2pgsql")
        pntTbl = shp_to_psql(conDB,  pntShp, api="shp2pgsql")
        
        # Get result
        outTbl = split_lines_on_pnt(
            conDB, lnhTbl, pntTbl, get_filename(outShp, forceLower=True),
            lnhidonpnt, 'gid'
        )
        
        # Export result
        result = dbtbl_to_shp(
            conDB, outTbl, "geom", outShp, inDB='psql', tableIsQuery=None,
            api="pgsql2shp"
        )
    
    else:
        raise ValueError(
            "API {} is not available".format(api)
        )
    
    return result
