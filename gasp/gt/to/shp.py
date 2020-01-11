"""
Something to Feature Class
"""


"""
Python data to SHP
"""

def df_to_shp(indf, outShp):
    """
    Pandas Dataframe to ESRI Shapefile
    """
    
    import geopandas
    
    indf.to_file(outShp)
    
    return outShp


def obj_to_shp(dd, geomkey, srs, outshp):
    from gasp.gt.to.geom import df_to_geodf as obj_to_geodf
    
    geodf = obj_to_geodf(dd, geomkey, srs)
    
    return df_to_shp(geodf, outshp)


"""
File to SHP
"""

def shp_to_shp(inShp, outShp, gisApi='ogr', supportForSpatialLite=None):
    """
    Convert a vectorial file to another with other file format
    
    API's Available:
    * ogr;
    
    When using gisApi='ogr' - Set supportForSpatialLite to True if outShp is
    a sqlite db and if you want SpatialLite support for that database.
    """
    
    import os
    
    if gisApi == 'ogr':
        from gasp            import exec_cmd
        from gasp.gt.prop.ff import drv_name
        
        out_driver = drv_name(outShp)
    
        if out_driver == 'SQLite' and supportForSpatialLite:
            splite = ' -dsco "SPATIALITE=YES"'
        else:
            splite = ''
    
        cmd = 'ogr2ogr -f "{drv}" {out} {_in}{lite}'.format(
            drv=out_driver, out=outShp, _in=inShp,
            lite=splite
        )
    
        # Run command
        cmdout = exec_cmd(cmd)
    
    else:
        raise ValueError('Sorry, API {} is not available'.format(gisApi))
    
    return outShp


def foldershp_to_foldershp(inFld, outFld, destiny_file_format,
                           file_format='.shp', useApi='ogr'):
    """
    Execute shp_to_shp for every file in inFld (path to folder)
    
    useApi options:
    * ogr;
    """
    
    import os
    from gasp.pyt.oss import lst_ff, get_filename
    
    if not os.path.exists(outFld):
        from gasp.pyt.oss import create_folder
        create_folder(outFld)
    
    geo_files = lst_ff(inFld, file_format=file_format)
    
    for f in geo_files:
        shp_to_shp(f, os.path.join(outFld, '{}.{}'.format(
            get_filename(f), destiny_file_format if \
                destiny_file_format[0] == '.' else '.' + destiny_file_format
        )), gisApi=useApi)
    
    return outFld


def shps_to_shp(shps, outShp, api="ogr2ogr", fformat='.shp'):
    """
    Get all features in several Shapefiles and save them in one file
    """

    import os

    if type(shps) != list:
        # Check if is dir
        if os.path.isdir(shps):
            from gasp.pyt.oss import lst_ff
            # List shps in dir

            shps = lst_ff(shps, file_format=fformat)
        else:
            raise ValueError((
                'shps should be a list with paths for Feature Classes or a path to '
                'folder with Feature Classes'
            ))

    
    if api == "ogr2ogr":
        from gasp            import exec_cmd
        from gasp.gt.prop.ff import drv_name
        
        out_drv = drv_name(outShp)
        
        # Create output and copy some features of one layer (first in shps)
        cmdout = exec_cmd('ogr2ogr -f "{}" {} {}'.format(
            out_drv, outShp, shps[0]
        ))
        
        # Append remaining layers
        lcmd = [exec_cmd(
            'ogr2ogr -f "{}" -update -append {} {}'.format(
                out_drv, outShp, shps[i]
            )
        ) for i in range(1, len(shps))]
    
    elif api == 'pandas':
        """
        Merge SHP using pandas
        """
        
        from gasp.fm        import tbl_to_obj
        from gasp.gt.to.shp import df_to_shp
        
        if type(shps) != list:
            raise ValueError('shps should be a list with paths for Feature Classes')
        
        dfs = [tbl_to_obj(shp) for shp in shps]
        
        result = dfs[0]
        
        for df in dfs[1:]:
            result = result.append(df, ignore_index=True, sort=True)
        
        df_to_shp(result, outShp)
    
    else:
        raise ValueError(
            "{} API is not available"
        )
    
    return outShp


def same_attr_to_shp(inShps, interestCol, outFolder, basename="data_",
                     resultDict=None):
    """
    For several SHPS with the same field, this program will list
    all values in such field and will create a new shp for all
    values with the respective geometry regardeless the origin shp.
    """
    
    import os
    from gasp.pyt       import obj_to_lst
    from gasp.fm        import tbl_to_obj
    from gasp.df.mng    import merge_df
    from gasp.gt.to.shp import df_to_shp
    
    EXT = os.path.splitext(inShps[0])[1]
    
    shpDfs = [tbl_to_obj(shp) for shp in inShps]
    
    DF = merge_df(shpDfs, ignIndex=True)
    #DF.dropna(axis=0, how='any', inplace=True)
    
    uniqueVal = DF[interestCol].unique()
    
    nShps = [] if not resultDict else {}
    for val in uniqueVal:
        ndf = DF[DF[interestCol] == val]
        
        KEY = str(val).split('.')[0] if '.' in str(val) else str(val)
        
        nshp = df_to_shp(ndf, os.path.join(
            outFolder, '{}{}{}'.format(basename, KEY, EXT)
        ))
        
        if not resultDict:
            nShps.append(nshp)
        else:
            nShps[KEY] = nshp
    
    return nShps


def osm_to_featcls(xmlOsm, output, fileFormat='.shp', useXmlName=None,
                   outepsg=4326):
    """
    OSM to ESRI Shapefile
    """

    import os
    from gasp.gt.anls.exct import sel_by_attr
    from gasp.pyt.oss      import get_filename, del_file
    
    # Convert xml to sqliteDB
    sqDB = shp_to_shp(xmlOsm, os.path.join(output, 'fresh_osm.sqlite'))

    # sqliteDB to Feature Class
    TABLES = {'points' : 'pnt', 'lines' : 'lnh',
              'multilinestrings' : 'mlnh', 'multipolygons' : 'poly'}
    
    for T in TABLES:
        sel_by_attr(
            sqDB, "SELECT * FROM {}".format(T),
            os.path.join(output, "{}{}{}".format(
                "" if not useXmlName else get_filename(xmlOsm) + "_",
                TABLES[T],
                fileFormat if fileFormat[0] == '.' else "." + fileFormat
            )), api_gis='ogr', oEPSG=None if outepsg == 4326 else outepsg,
            iEPSG=4326
        )
    
    # Del temp DB
    del_file(sqDB)

    return output


def getosm_to_featcls(inBoundary, outVector, boundaryEpsg=4326,
                         vectorFormat='.shp'):
    """
    Get OSM Data from the Internet and convert the file to regular vector file
    """

    import os; from gasp.gt.to.osm import download_by_boundary

    # Download data from the web
    osmData = download_by_boundary(
        inBoundary, os.path.dirname(outVector), 'fresh_osm',
        boundaryEpsg, GetUrl=None
    )

    # Convert data to regular vector file
    return osm_to_featcls(
        osmData, outVector, fileFormat=vectorFormat
    )


def eachfeat_to_newshp(inShp, outFolder, epsg=None, idCol=None):
    """
    Export each feature in inShp to a new/single File
    """
    
    import os; from osgeo  import ogr
    from gasp.gt.prop.ff   import drv_name
    from gasp.gt.prop.feat import get_gtype, lst_fld
    from gasp.gt.lyr.fld   import copy_flds
    from gasp.pyt.oss      import get_fileformat, get_filename
    
    inDt = ogr.GetDriverByName(
        drv_name(inShp)).Open(inShp)
    
    lyr = inDt.GetLayer()
    
    # Get SRS for the output
    if not epsg:
        from gasp.gt.prop.prj import get_shp_sref
        srs = get_shp_sref(lyr)
    
    else:
        from gasp.gt.prop.prj import get_sref_from_epsg
        srs = get_sref_from_epsg(epsg)
    
    # Get fields name
    fields = lst_fld(lyr)
    
    # Get Geometry type
    geomCls = get_gtype(inShp, gisApi='ogr', name=None, py_cls=True)
    
    # Read features and create a new file for each feature
    RESULT_SHP = []
    for feat in lyr:
        # Create output
        newShp = os.path.join(outFolder, "{}_{}{}".format(
            get_filename(inShp),
            str(feat.GetFID()) if not idCol else str(feat.GetField(idCol)),
            get_fileformat(inShp)
        ))
        
        newData = ogr.GetDriverByName(
            drv_name(newShp)).CreateDataSource(newShp)
        
        newLyr = newData.CreateLayer(
            str(get_filename(newShp)), srs, geom_type=geomCls
        )
        
        # Copy fields from input to output
        copy_flds(lyr, newLyr)
        
        newLyrDefn = newLyr.GetLayerDefn()
        
        # Create new feature
        newFeat = ogr.Feature(newLyrDefn)
        
        # Copy geometry
        geom = feat.GetGeometryRef()
        newFeat.SetGeometry(geom)
        
        # Set fields attributes
        for fld in fields:
            newFeat.SetField(fld, feat.GetField(fld))
        
        # Save feature
        newLyr.CreateFeature(newFeat)
        
        newFeat.Destroy()
        
        del newLyr
        newData.Destroy()
        RESULT_SHP.append(newShp)
    
    return RESULT_SHP


"""
GRASS GIS conversions
"""

def shp_to_grs(inLyr, outLyr, filterByReg=None, asCMD=None):
    """
    Add Shape to GRASS GIS
    """
    
    if not asCMD:
        from grass.pygrass.modules import Module
        
        f = 'o' if not filterByReg else 'ro'
        
        m = Module(
            "v.in.ogr", input=inLyr, output=outLyr, flags='o',
            overwrite=True, run_=False, quiet=True
        )
        
        m()
    
    else:
        from gasp import exec_cmd
        
        rcmd = exec_cmd((
            "v.in.ogr input={} output={} -o{} --overwrite --quiet"
        ).format(inLyr, outLyr, " -r" if filterByReg else ""))
    
    return outLyr


def grs_to_shp(inLyr, outLyr, geomType, lyrN=1, asCMD=True, asMultiPart=None):
    """
    GRASS Vector to Shape File
    """
    
    from gasp.gt.prop.ff import VectorialDrivers
    from gasp.pyt.oss    import get_fileformat
    
    vecDriv = VectorialDrivers()
    outEXT  = get_fileformat(outLyr)
    
    if not asCMD:
        from grass.pygrass.modules import Module
        
        __flg = None if not asMultiPart else 'm'
        
        m = Module(
            "v.out.ogr", input=inLyr, type=geomType, output=outLyr,
            format=vecDriv[outEXT], flags=__flg, layer=lyrN,
            overwrite=True, run_=False, quiet=True
        )
        
        m()
    
    else:
        from gasp import exec_cmd
        
        rcmd = exec_cmd((
            "v.out.ogr input={} type={} output={} format={} "
            "layer={}{} --overwrite --quiet"  
        ).format(
            inLyr, geomType, outLyr, 
            vecDriv[outEXT], lyrN, " -m" if asMultiPart else ""
        ))
    
    return outLyr


"""
Database Table to Shape
"""

def dbtbl_to_shp(db, tbl, geom_col, outShp, where=None, inDB='psql',
                 notTable=None, filterByReg=None, outShpIsGRASS=None,
                 tableIsQuery=None, api='psql', epsg=None):
    """
    Database Table to Feature Class file
    
    idDB Options:
    * psql
    * sqlite
    
    api Options:
    * psql
    * sqlite
    * pgsql2shp
    
    if outShpIsGRASS if true, the method assumes that outShp is
    a GRASS Vector. That implies that a GRASS Session was been
    started already. 
    """
    
    if outShpIsGRASS:
        from gasp import exec_cmd
        
        whr = "" if not where else "where=\"{}\"".format(where)
        
        cmd_str = (
            "v.in.ogr input=\"PG:host={} dbname={} user={} password={} "
            "port={}\" output={} layer={} geometry={}{}{}{} -o --overwrite --quiet"
        ).format(
            db["HOST"], db["DATABASE"], db["USER"], db["PASSWORD"],
            db["PORT"], outShp, tbl, geom_col, whr,
            " -t" if notTable else "", " -r" if filterByReg else ""
        ) if inDB == 'psql' else (
            "v.in.ogr -o -input={} layer={} output={}{}{}{}"
        ).format(db, tbl, outShp, whr,
            " -t" if notTable else "", " -r" if filterByReg else ""
        ) if inDB == 'sqlite' else None
        
        rcmd = exec_cmd(cmd_str)
    
    else:
        if api == 'pgsql2shp':
            from gasp import exec_cmd
            
            outcmd = exec_cmd((
                'pgsql2shp -f {out} -h {hst} -u {usr} -p {pt} -P {pas}{geom} '
                '{bd} {t}'
            ).format(
                hst=db['HOST'], usr=db["USER"], pt=db["PORT"],
                pas=db['PASSWORD'], bd=db['DATABASE'], out=outShp,
                t=tbl if not tableIsQuery else '"{}"'.format(tbl),
                geom="" if not geom_col else " -g {}".format(geom_col)
            ))
        
        elif api == 'psql' or api == 'sqlite':
            from gasp.sql.fm import Q_to_df
            
            q = "SELECT * FROM {}".format(tbl) if not tableIsQuery else tbl
            
            df = Q_to_df(db, q, db_api=api, geomCol=geom_col, epsg=epsg)
            
            outsh = df_to_shp(df, outShp)
        
        else:
            raise ValueError((
                'api value must be \'psql\', \'sqlite\' or \'pgsql2shp\''))
    
    return outShp


"""
Numerical to Shape
"""

def coords_to_boundshp(topLeft, lowerRight, epsg, outshp,
                       outEpsg=None):
    """
    Top Left and Lower Right to Boundary
    """
    
    import os; from osgeo import ogr
    from gasp.gt.prop.ff  import drv_name
    from gasp.gt.prop.prj import get_sref_from_epsg
    from gasp.pyt.oss     import get_filename
    from gasp.g.to        import coords_to_boundary

    # Get boundary geometry
    polygon = coords_to_boundary(topLeft, lowerRight, epsg, outEpsg=outEpsg)
    
    # Create outShapefile if a path is given
    shp = ogr.GetDriverByName(
        drv_name(outshp)).CreateDataSource(outshp)
    
    SRS_OBJ = get_sref_from_epsg(epsg) if not outEpsg else \
        get_sref_from_epsg(outEpsg)
    lyr = shp.CreateLayer(
        get_filename(outshp), SRS_OBJ, geom_type=ogr.wkbPolygon
    )
    
    outDefn = lyr.GetLayerDefn()
    
    feat = ogr.Feature(outDefn)
    
    feat.SetGeometry(polygon)
    lyr.CreateFeature(feat)
    
    feat.Destroy()
    shp.Destroy()
    
    return outshp


"""
Extent to Shape
"""

def shpext_to_boundshp(inShp, outShp, epsg=None):
    """
    Read one feature class extent and create a boundary with that
    extent
    
    The outFile could be a Feature Class or one Raster Dataset
    """
    
    import os; from osgeo import ogr
    from gasp.gt.prop.ff  import drv_name
    from gasp.pyt.oss     import get_filename
    from gasp.gt.to.geom  import new_pnt
    from gasp.g.to        import shpext_to_boundary
    
    # Get SRS for the output
    if not epsg:
        from gasp.gt.prop.prj import get_shp_sref
        
        srs = get_shp_sref(inShp)
    
    else:
        from gasp.gt.prop.prj import get_sref_from_epsg
        
        srs= get_sref_from_epsg(epsg)
    
    # Write new file
    shp = ogr.GetDriverByName(
        drv_name(outShp)).CreateDataSource(outShp)
    
    lyr = shp.CreateLayer(
        get_filename(outShp, forceLower=True),
        srs, geom_type=ogr.wkbPolygon
    )
    
    outDefn = lyr.GetLayerDefn()
    
    feat = ogr.Feature(outDefn)
    polygon = shpext_to_boundary(inShp)
    
    feat.SetGeometry(polygon)
    lyr.CreateFeature(feat)
    
    feat.Destroy()
    shp.Destroy()
    
    return outShp


def pnts_to_boundary(pntShp, outBound, distMeters):
    """
    Create a boundary from Point using a tolerance in meters
    """
    
    from osgeo            import ogr
    from gasp.pyt.oss     import get_filename
    from gasp.gt.prop.ff  import drv_name
    from gasp.gt.to.geom  import new_pnt
    from gasp.gt.prop.prj import get_shp_sref
    
    SRS = get_shp_sref(pntShp)
    
    shp = ogr.GetDriverByName(drv_name(pntShp)).Open(pntShp)
    lyr = shp.GetLayer()
    
    outShp = ogr.GetDriverByName(drv_name(outBound)).CreateDataSource(outBound)
    outLyr = outShp.CreateLayer(
        get_filename(outBound, forceLower=True), SRS,
        geom_type=ogr.wkbPolygon
    )
    
    outDefn = outLyr.GetLayerDefn()
    
    for feat in lyr:
        __feat = ogr.Feature(outDefn)
        ring = ogr.Geometry(ogr.wkbLinearRing)
        
        geom = feat.GetGeometryRef()
        X, Y = geom.GetX(), geom.GetY()
        
        boundary_points = [
            new_pnt(X - distMeters, Y + distMeters), # Topleft
            new_pnt(X + distMeters, Y + distMeters), # TopRight
            new_pnt(X + distMeters, Y - distMeters), # Lower Right
            new_pnt(X - distMeters, Y - distMeters), # Lower Left
            new_pnt(X - distMeters, Y + distMeters)
        ]
        
        for pnt in boundary_points:
            ring.AddPoint(pnt.GetX(), pnt.GetY())
        
        polygon = ogr.Geometry(ogr.wkbPolygon)
        polygon.AddGeometry(ring)
        
        __feat.SetGeometry(polygon)
        
        outLyr.CreateFeature(__feat)
        
        feat.Destroy()
        
        __feat  = None
        ring    = None
        polygon = None
    
    shp.Destroy()
    outShp.Destroy()
    
    return outBound


def rstext_to_shp(inRst, outShp, epsg=None):
    """
    Raster Extent to Feature Class
    """
    
    from gasp.gt.prop.rst import rst_ext
    
    # Get Raster Extent
    left, right, bottom, top = rst_ext(inRst)
    
    # Get EPSG
    if not epsg:
        from gasp.gt.prop.prj import get_rst_epsg
        
        epsg = get_rst_epsg(inRst)
    
    # Create Boundary
    return coords_to_boundshp((left, top), (right, bottom), epsg, outShp)


"""
Raster to Feature Class
"""

def rst_to_polyg(inRst, outShp, rstColumn=None, gisApi='gdal', epsg=None):
    """
    Raster to Polygon Shapefile
    
    Api's Available:
    * gdal;
    * qgis;
    * pygrass;
    * grasscmd
    """
    
    if gisApi == 'gdal':
        if not epsg:
            raise ValueError((
                'Using GDAL, you must specify the EPSG CODE of the '
                'Spatial Reference System of input raster.'
            ))
        
        import os;from osgeo import gdal, ogr, osr
        from gasp.gt.prop.ff import drv_name
        from gasp.pyt.oss    import get_filename
        
        src = gdal.Open(inRst)
        bnd = src.GetRasterBand(1)
        
        output = ogr.GetDriverByName(drv_name(ouShp)).CreateDataSource(outShp)
        
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(epsg)
        
        lyr = output.CreateLayer(get_filename(outShp, forceLower=True), srs)
        
        lyr.CreateField(ogr.FieldDefn('VALUE', ogr.OFTInteger))
        gdal.Polygonize(bnd, None, lyr, 0, [], callback=None)
        
        output.Destroy()
    
    elif gisApi == 'qgis':
        import processing
        
        processing.runalg(
            "gdalogr:polygonize", inRst, "value", outShp
        )
    
    elif gisApi == 'pygrass':
        from grass.pygrass.modules import Module
        
        rstField = "value" if not rstColumn else rstColumn
        
        rtop = Module(
            "r.to.vect", input=inRst, output=outShp, type="area",
            column=rstField, overwrite=True, run_=False, quiet=True
        )
        rtop()
    
    elif gisApi == 'grasscmd':
        from gasp import exec_cmd
        
        rstField = "value" if not rstColumn else rstColumn
        
        rcmd = exec_cmd((
            "r.to.vect input={} output={} type=area column={} "
            "--overwrite --quiet"
        ).format(inRst, outShp, rstField))
    
    else:
        raise ValueError('Sorry, API {} is not available'.format(gisApi))
    
    return outShp

"""
Excel to SHP
"""

def pointXls_to_shp(xlsFile, outShp, x_col, y_col, epsg, sheet=None):
    """
    Excel table with Point information to ESRI Shapefile
    """
    
    from gasp.fm         import tbl_to_obj
    from gasp.gt.to.geom import pnt_dfwxy_to_geodf
    from gasp.gt.to.shp  import df_to_shp
    
    # XLS TO PANDAS DATAFRAME
    dataDf = tbl_to_obj(xlsFile, sheet=sheet)
    
    # DATAFRAME TO GEO DATAFRAME
    geoDataDf = pnt_dfwxy_to_geodf(dataDf, x_col, y_col, epsg)
    
    # GEODATAFRAME TO ESRI SHAPEFILE
    df_to_shp(geoDataDf, outShp)
    
    return outShp

