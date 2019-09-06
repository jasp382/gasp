"""
Topological Tools
"""

"""
Object Based
"""

def point_in_polygon(point, polygon):
    """
    Point is Inside Polygon?
    """
    
    return point.Within(polygon)


"""
File Based
"""
def snap_points_to_near_line(lineShp, pointShp, epsg, workGrass,
                             outPoints, location='overlap_pnts', api='grass',
                             movesShp=None):
    """
    Move points to overlap near line
    
    API's Available:
    * grass;
    * saga.
    """
    
    if api == 'grass':
        """
        Uses GRASS GIS to find near lines.
        """
        
        import os;             import numpy
        from geopandas         import GeoDataFrame
        from gasp3.pyt.oss     import get_filename
        from gasp3.gt.wenv.grs import run_grass
        from gasp3.dt.fm       import tbl_to_obj as shp_to_df
        from gasp3.dt.to.shp   import df_to_shp
    
        # Create GRASS GIS Location
        grassBase = run_grass(workGrass, location=location, srs=epsg)
    
        import grass.script as grass
        import grass.script.setup as gsetup
        gsetup.init(grassBase, workGrass, location, 'PERMANENT')
    
        # Import some GRASS GIS tools
        from gasp3.gt.anls.prox import grs_near as near
        from gasp3.gt.mng.tbl   import geomattr_to_db
        from gasp3.dt.to.shp    import shp_to_grs, grs_to_shp
    
        # Import data into GRASS GIS
        grsLines = shp_to_grs(
            lineShp, get_filename(lineShp, forceLower=True)
        )
    
        grsPoint = shp_to_grs(
            pointShp, get_filename(pointShp, forceLower=True)
        )
    
        # Get distance from points to near line
        near(grsPoint, grsLines, nearCatCol="tocat", nearDistCol="todistance")
    
        # Get coord of start/end points of polylines
        geomattr_to_db(grsLines, ['sta_pnt_x', 'sta_pnt_y'], 'start', 'line')
        geomattr_to_db(grsLines, ['end_pnt_x', 'end_pnt_y'],   'end', 'line')
    
        # Export data from GRASS GIS
        ogrPoint = grs_to_shp(grsPoint, os.path.join(
            workGrass, grsPoint + '.shp', 'point', asMultiPart=True
        ))

        ogrLine = grs_to_shp(grsLines, os.path.join(
            workGrass, grsLines + '.shp', 'point', asMultiPart=True
        ))
    
        # Points to GeoDataFrame
        pntDf = tbl_to_obj(ogrPoint)
        # Lines to GeoDataFrame
        lnhDf = tbl_to_obj(ogrLine)
    
        # Erase unecessary fields
        pntDf.drop(["todistance"], axis=1, inplace=True)
        lnhDf.drop([c for c in lnhDf.columns.values if c != 'geometry' and 
                    c != 'cat' and c != 'sta_pnt_x' and c != 'sta_pnt_y' and 
                    c != 'end_pnt_x' and c != 'end_pnt_y'],
                    axis=1, inplace=True)
    
        # Join Geometries - Table with Point Geometry and Geometry of the 
        # nearest line
        resultDf = pntDf.merge(
            lnhDf, how='inner', left_on='tocat', right_on='cat')
    
        # Move points
        resultDf['geometry'] = [geoms[0].interpolate(
            geoms[0].project(geoms[1])
        ) for geoms in zip(resultDf.geometry_y, resultDf.geometry_x)]
    
        resultDf.drop(["geometry_x", "geometry_y", "cat_x", "cat_y"],
                      axis=1, inplace=True)
    
        resultDf = GeoDataFrame(
            resultDf, crs={"init" : 'epsg:{}'.format(epsg)}, geometry="geometry"
        )
    
        # Check if points are equal to any start/end points
        resultDf["x"] = resultDf.geometry.x
        resultDf["y"] = resultDf.geometry.y
    
        resultDf["check"] = numpy.where(
            (resultDf["x"] == resultDf["sta_pnt_x"]) & (resultDf["y"] == resultDf["sta_pnt_y"]),
            1, 0
        )
    
        resultDf["check"] = numpy.where(
            (resultDf["x"] == resultDf["end_pnt_x"]) & (resultDf["y"] == resultDf["end_pnt_y"]),
            1, 0
        )
    
        # To file
        df_to_shp(resultDf, outPoints)
    
    elif api == 'saga':
        """
        Snap Points to Lines using SAGA GIS
        """
        
        from gasp3 import exec_cmd
        
        cmd = (
            "saga_cmd shapes_points 19 -INPUT {pnt} -SNAP {lnh} "
            "-OUTPUT {out}{mv}"
        ).format(
            pnt=pointShp, lnh=lineShp, out=outPoints,
            mv="" if not movesShp else " -MOVES {}".format(movesShp)
        )
        
        outcmd = exec_cmd(cmd)
    
    else:
        raise ValueError("{} is not available!".format(api))
    
    return outPoints


def break_lines_on_points(lineShp, pointShp, lineIdInPntShp,
                         splitedShp, srsEpsgCode):
    """
    Break lines on points location
    
    The points should be contained by the lines;
    The points table should have a column with the id of the
    line that contains the point.
    """
    
    from shapely.ops      import split
    from shapely.geometry import Point, LineString
    from gasp3.dt.fm      import tbl_to_obj
    from gasp3.pyt.df.mng import col_list_val_to_row
    from gasp3.dt.to.shp  import df_to_shp
    from gasp3.dt.to.obj  import dict_to_df
    
    # Sanitize line geometry
    def fix_line(line, point):
        buff = point.buffer(0.0001)
        
        splitLine = split(line, buff)
        
        nline = LineString(
            list(splitLine[0].coords) + list(point.coords) +
            list(splitLine[-1].coords)
        )
        
        return nline
    
    pnts  = tbl_to_obj(pointShp, fields='ALL', output='array')
    lines = tbl_to_obj(lineShp, fields='ALL', output='dict')
    
    for point in pnts:
        rel_line = lines[point[lineIdInPntShp]]
        
        if type(rel_line["GEOM"]) != list:
            line_geom = fix_line(rel_line["GEOM"], point["GEOM"])
            
            split_lines = split(line_geom, point["GEOM"])
            
            lines[point[lineIdInPntShp]]["GEOM"] = [l for l in split_lines]
        
        else:
            for i in range(len(rel_line["GEOM"])):
                if rel_line["GEOM"][i].distance(point["GEOM"]) < 1e-8:
                    line_geom = fix_line(rel_line["GEOM"][i], point["GEOM"])
                    split_lines = split(line_geom, point["GEOM"])
                    split_lines = [l for l in split_lines]
                    
                    lines[point[lineIdInPntShp]]["GEOM"][i] = split_lines[0]
                    lines[point[lineIdInPntShp]]["GEOM"] += split_lines[1:]
                    
                    break
                
                else:
                    continue
    
    # Result to Dataframe
    linesDf = dict_to_df(lines)
    
    # Where GEOM is a List, create a new row for each element in list
    linesDf = col_list_val_to_row(
        linesDf, "GEOM", geomCol="GEOM", epsg=srsEpsgCode
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
        from gasp.fm import points_to_list
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
    """
    
    import os
    from gasp3.dt.to.sql   import shp_to_psql
    from gasp3.dt.to.shp   import psql_to_shp
    from gasp3.gt.wenv.grs import run_grass
    from gasp3.pyt.oss     import get_filename
    from gasp3.sql.mng.db  import create_db
    from gasp3.sql.mng.tbl import q_to_ntbl
    
    tmpFiles = os.path.join(workspace, loc)
    
    gbase = run_grass(workspace, location=loc, srs=srs)
    
    import grass.script       as grass
    import grass.script.setup as gsetup
    
    gsetup.init(gbase, workspace, loc, 'PERMANENT')
    
    from gasp3.dt.to.shp import shp_to_grs, grs_to_shp
    
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
        conParam, LINES, srs,
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
    
    psql_to_shp(
        conParam,  CORR_LINES, out_correct,
        api="pgsql2shp", geom_col="geom"
    )
    
    psql_to_shp(
        conParam, ERROR_LINES, out_tocorrect,
        api="pgsql2shp", geom_col="geom"
    )


def orig_dest_to_polyline(srcPoints, srcField, 
                          destPoints, destField, outShp):
    """
    Connect origins to destinations with a polyline which
    length is the minimum distance between the origin related
    with a specific destination.
    
    One origin should be related with one destination.
    These relations should be expressed in srcField and destField
    """
    
    from geopandas        import GeoDataFrame
    from shapely.geometry import LineString
    from gasp3.dt.fm      import tbl_to_obj
    from gasp3.dt.to.shp  import df_to_shp
    
    srcPnt = tbl_to_obj(srcPoints)
    desPnt = tbl_to_obj(destPoints)
    
    joinDf = srcPnt.merge(destPnt, how='inner',
                          left_on=srcField, right_on=destField)
    
    joinDf["geometry"] = joinDf.apply(
        lambda x: LineString(
            x["geometry_x"], x["geometry_y"]
        ), axis=1
    )
    
    joinDf.drop(["geometry_x", "geometry_y"], axis=1, inplace=True)
    
    a = GeoDataFrame(joinDf)
    
    df_to_shp(joinDf, outShp)
    
    return outShp

