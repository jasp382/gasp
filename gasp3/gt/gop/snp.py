"""
Snapping
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
        from gasp3.fm          import tbl_to_obj as shp_to_df
        from gasp3.gt.to.shp   import df_to_shp
    
        # Create GRASS GIS Location
        grassBase = run_grass(workGrass, location=location, srs=epsg)
    
        import grass.script as grass
        import grass.script.setup as gsetup
        gsetup.init(grassBase, workGrass, location, 'PERMANENT')
    
        # Import some GRASS GIS tools
        from gasp3.gt.anls.prox import grs_near as near
        from gasp3.gt.mng.tbl   import geomattr_to_db
        from gasp3.gt.to.shp    import shp_to_grs, grs_to_shp
    
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

