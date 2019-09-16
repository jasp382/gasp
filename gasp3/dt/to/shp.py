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
    from gasp3.dt.to.geom import df_to_geodf as obj_to_geodf
    
    geodf = obj_to_geodf(dd, geomkey, srs)
    
    return df_to_shp(geodf, outshp)


def array_to_shp(array_like, outFile, x='x', y='y', epsg=None):
    """
    Convert a array with geometric data into a file with geometry (GML, ESRI
    Shapefile or others).
    
    Example of an array_like object:
    data = [
        {col_1: value, col_2: value, x: value, y: value},
        {col_1: value, col_2: value, x: value, y: value},
    ]
    
    This array must contain a 'x' and 'y' keys (or 
    equivalent).
    
    TODO: Now works only for points
    """
    
    import os; from osgeo  import ogr
    from gasp3.dt.to.geom  import create_point
    from gasp3.gt.prop.ff  import drv_name
    from gasp3.gt.prop.prj import get_sref_from_epsg
    from gasp3.gt.prop.fld import map_pyType_fldCode
    from gasp3.pyt.oss     import get_filename
    
    ogr.UseExceptions()
    
    # Create output file
    shp = ogr.GetDriverByName(drv_name(outFile)).CreateDataSource(outFile)
    
    lyr = shp.CreateLayer(
        get_filename(outFile),
        None if not epsg else get_sref_from_epsg(epsg),
        geom_type=ogr.wkbPoint,
    )
    
    # Create fields of output file
    fields = []
    keys_fields = {}
    for k in array_like[0]:
        if k != x and k != y:
            fld_name = k[:9]
            
            if fld_name not in fields:
                fields.append(fld_name)
            
            else:
                # Get All similar fields in the fields list
                tmp_fld = []
                for i in fields:
                    if i[:8] == fld_name[:8]:
                        tmp_fld.append(i[:8])
                
                c = len(tmp_fld)
                
                fld_name = fld_name[:8] + '_{n}'.format(n=str(c))
                
                fields.append(fld_name)
            
            # TODO: Automatic mapping of filters types needs further testing
            #fld_type = map_pyType_fldCode(array_like[0][k])
            lyr.CreateField(
                ogr.FieldDefn(fld_name, ogr.OFTString)
            )
            
            keys_fields[k] = fld_name
    
    defn = lyr.GetLayerDefn()
    
    for i in range(len(array_like)):
        feat = ogr.Feature(defn)
        feat.SetGeometry(
            create_point(array_like[i][x], array_like[i][y], api='ogr')
        )
        
        for k in array_like[i]:
            if k != x and k != y:
                value = array_like[i][k]
                
                if len(value) >= 254:
                    value = value[:253]
                
                feat.SetField(
                    keys_fields[k], value
                )
        
        lyr.CreateFeature(feat)
        
        feat = None
    
    shp.Destroy()
    
    return outFile


def shply_array_to_shp(arrayLike, outfile, geomType, epsg=None,
                       fields=None, crsObj=None):
    """
    Convert a array with Shapely geometric data into a file
    with geometry (GML, ESRI Shapefile or others).
    
    Example of an array_like object:
    data = [
        {col_1: value, col_2: value, geom: geomObj},
        {col_1: value, col_2: value, geom: geomObj},
    ]
    """
    
    import os; from osgeo  import ogr
    from gasp3.gt.prop.ff  import drv_name
    from gasp3.gt.prop.prj import get_sref_from_epsg
    
    # Create output file
    shp = ogr.GetDriverByName(
        drv_name(outfile)).CreateDataSource(outfile)
    
    lyr = shp.CreateLayer(
        os.path.splitext(os.path.basename(outfile))[0],
        get_sref_from_epsg(epsg) if epsg else crsObj if crsObj else \
            None, geom_type=geomType
    )
    
    # Create fields of output file
    # TODO: Automatic mapping of filters types needs further testing
    if fields:
        for f in fields:
            lyr.CreateField(ogr.FieldDefn(f, fields[f]))
    
    # Add features
    defn = lyr.GetLayerDefn()
    for feat in arrayLike:
        newFeat = ogr.Feature(defn)
        
        newFeat.SetGeometry(
            ogr.CreateGeometryFromWkb(feat['GEOM'].wkb)
        )
        
        if len(fields):
            for f in fields:
                newFeat.SetField(f, feat[f])
        
        lyr.CreateFeature(newFeat)
        
        newFeat = None
    
    shp.Destroy()
    
    return outfile


def shply_dict_to_shp(dictLike, outfile, geomType, epsg=None,
                      fields=None, crsObj=None):
    """
    Dict with shapely Geometries to Feature Class
    """
    
    import os; from osgeo  import ogr
    from gasp3.gt.prop.ff  import drv_name
    from gasp3.gt.prop.prj import get_sref_from_epsg
    from gasp3.pyt.oss     import get_filename
    
    # Create output file
    shp = ogr.GetDriverByName(
        drv_name(outfile)).CreateDataSource(outfile)
    
    lyr = shp.CreateLayer(get_filename(outfile),
        get_sref_from_epsg(epsg) if epsg else crsObj if \
            crsObj else None,
        geom_type=geomType
    )
    
    # Create fields of output file
    if fields:
        for f in fields:
            lyr.CreateField(ogr.FieldDefn(f, fields[f]))
    
    # Add features
    fids = dictLike.keys()
    fids.sort()
    defn = lyr.GetLayerDefn()
    for fid in fids:
        if type(dictLike[fid]["GEOM"]) == list:
            for geom in dictLike[fid]["GEOM"]:
                newFeat = ogr.Feature(defn)
        
                newFeat.SetGeometry(
                    ogr.CreateGeometryFromWkb(geom.wkb)
                )
                
                if len(fields):
                    for f in fields:
                        newFeat.SetField(f, dictLike[fid][f])
                
                lyr.CreateFeature(newFeat)
                
                newFeat = None
        
        else:
            newFeat = ogr.Feature(defn)
            
            newFeat.SetGeometry(
                ogr.CreateGeometryFromWkb(dictLike[fid]["GEOM"].wkb)
            )
            
            if len(fields):
                for f in fields:
                    newFeat.SetField(f, dictLike[fid][f])
                
            lyr.CreateFeature(newFeat)
            
            newFeat = None
    
    del lyr
    shp.Destroy()
    
    return outfile


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
        from gasp3            import exec_cmd
        from gasp3.gt.prop.ff import drv_name
        
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
    from gasp3.pyt.oss import list_files, get_filename
    
    if not os.path.exists(outFld):
        from gasp3.pyt.oss import create_folder
        create_folder(outFld)
    
    geo_files = list_files(inFld, file_format=file_format)
    
    for f in geo_files:
        shp_to_shp(f, os.path.join(outFld, '{}.{}'.format(
            get_filename(f), destiny_file_format if \
                destiny_file_format[0] == '.' else '.' + destiny_file_format
        )), gisApi=useApi)
    
    return outFld


def osm_to_featurecls(xmlOsm, output, fileFormat='.shp', useXmlName=None):
    """
    OSM to ESRI Shapefile
    """

    import os
    from gasp3.gt.anls.exct import sel_by_attr
    
    # Convert xml to sqliteDB
    sqDB = ogr_btw_driver(xmlOsm, os.path.join(output, 'fresh_osm.sqlite'))

    # sqliteDB to Feature Class
    TABLES = ['points', 'lines', 'multilinestrings', 'multipolygons']
    
    for T in TABLES:
        sel_by_attr(
            sqDB, "SELECT * FROM {}".format(T),
            os.path.join(output, "{}{}{}".format(
                "" if not useXmlName else os.path.splitext(os.path.basename(xmlOsm))[0],
                T, fileFormat if fileFormat[0] == '.' else "." + fileFormat
            )), api_gis='ogr'
        )

    return output


def getosm_to_featurecls(inBoundary, outVector, boundaryEpsg=4326,
                         vectorFormat='.shp'):
    """
    Get OSM Data from the Internet and convert the file to regular vector file
    """

    import os
    from gasp3.dt.osm import download_by_boundary

    # Download data from the web
    osmData = download_by_boundary(
        inBoundary, os.path.join(outVector, 'fresh_osm.xml'), boundaryEpsg
    )

    # Convert data to regular vector file
    return osm_to_featurecls(
        osmData, outVector, fileFormat=vectorFormat
    )


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
        from gasp3 import exec_cmd
        
        rcmd = exec_cmd((
            "v.in.ogr input={} output={} -o{} --overwrite --quiet"
        ).format(inLyr, outLyr, " -r" if filterByReg else ""))
    
    return outLyr


def psql_to_grs(conParam, table, outLyr, where=None, notTable=None,
                filterByReg=None):
    """
    Add Shape to GRASS GIS from PGSQL
    """
    
    from gasp3 import exec_cmd
    
    rcmd = exec_cmd((
        "v.in.ogr input=\"PG:host={} dbname={} user={} password={} "
        "port={}\" output={} layer={}{}{}{} -o --overwrite --quiet" 
    ).format(conParam["HOST"], conParam["DATABASE"], conParam["USER"],
        conParam["PASSWORD"], conParam["PORT"], outLyr, table,
        "" if not where else " where=\"{}\"".format(where),
        " -t" if notTable else "",
        " -r" if filterByReg else ""
    ))
    
    return outLyr


def grs_to_shp(inLyr, outLyr, geomType, lyrN=1, asCMD=True, asMultiPart=None):
    """
    GRASS Vector to Shape File
    """
    
    from gasp3.gt.prop.ff import VectorialDrivers
    from gasp3.pyt.oss    import get_fileformat
    
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
        from gasp3 import exec_cmd
        
        rcmd = exec_cmd((
            "v.out.ogr input={} type={} output={} format={} "
            "layer={}{} --overwrite --quiet"  
        ).format(
            inLyr, geomType, outLyr, 
            vecDriv[outEXT], lyrN, " -m" if asMultiPart else ""
        ))
    
    return outLyr


def sqlite_to_grs(db, table, out, where=None, notTable=None,
                  filterByReg=None):
    """
    Execute a query on SQLITE DB and add data to GRASS GIS
    """
    
    from gasp3 import exec_cmd
    
    outCmd = exec_cmd(
        "v.in.ogr -o input={} layer={} output={}{}{}{}".format(
            db, table, out,
            "" if not where else " where=\"{}\"".format(where),
            " -t" if notTable else "",
            " -r" if filterByReg else ""
        )
    )
    
    return out


"""
Database Table to Shape
"""

def psql_to_shp(conParam, table, outshp, api='pandas',
                epsg=None, geom_col='geom', tableIsQuery=None):
    """
    PostgreSQL table to ESRI Shapefile using Pandas or PGSQL2SHP
    """
    
    if api == 'pandas':
        from gasp3.dt.fm.sql import psql_to_geodf
    
        q = "SELECT * FROM {}".format(table) if not tableIsQuery else table
    
        df = psql_to_geodf(conParam, q, geomCol=geom_col, epsg=epsg)
    
        outsh = df_to_shp(df, outshp)
    
    elif api == 'pgsql2shp':
        from gasp3 import exec_cmd
        
        cmd = (
            'pgsql2shp -f {out} -h {hst} -u {usr} -p {pt} -P {pas}{geom} '
            '{bd} {t}'
        ).format(
            hst=conParam['HOST'], usr=conParam['USER'], pt=conParam['PORT'],
            pas=conParam['PASSWORD'], bd=conParam['DATABASE'],
            t=table if not tableIsQuery else '"{}"'.format(table),
            out=outshp, geom="" if not geom_col else " -g {}".format(geom_col)
        )
        
        outcmd = exec_cmd(cmd)
    
    else:
        raise ValueError('api value must be \'pandas\' or \'pgsql2shp\'')
    
    return outshp


"""
Numerical to Shape
"""

def coords_to_boundary(topLeft, lowerRight, epsg, outshp,
                       outEpsg=None):
    """
    Top Left and Lower Right to Boundary
    """
    
    import os
    from osgeo             import ogr
    from gasp3.gt.prop.ff  import drv_name
    from gasp3.gt.prop.prj import get_sref_from_epsg
    from gasp3.pyt.oss     import get_filename
    
    boundary_points = [
        (   topLeft[0],    topLeft[1]),
        (lowerRight[0],    topLeft[1]),
        (lowerRight[0], lowerRight[1]),
        (   topLeft[0], lowerRight[1]),
        (   topLeft[0],    topLeft[1])
    ]
    
    # Convert SRS if outEPSG
    if outEpsg and epsg != outEpsg:
        from gasp3.dt.to.geom import create_polygon
        from gasp3.gt.mng.prj import project_geom
        
        poly = project_geom(
            create_polygon(boundary_points), epsg, outEpsg)
        
        left, right, bottom, top = poly.GetEnvelope()
        #bottom, top, left, right  = poly.GetEnvelope()
        
        boundary_points = [
            (left, top), (right, top), (right, bottom),
            (left, bottom), (left, top)
        ]
    
    # Create Geometry
    ring = ogr.Geometry(ogr.wkbLinearRing)
    for pnt in boundary_points:
        ring.AddPoint(pnt[0], pnt[1])
    
    polygon = ogr.Geometry(ogr.wkbPolygon)
    polygon.AddGeometry(ring)
    
    if not outshp:
        return polygon
    
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

def shpext_to_boundary(inShp, outShp, epsg=None):
    """
    Read one feature class extent and create a boundary with that
    extent
    
    The outFile could be a Feature Class or one Raster Dataset
    """
    
    import os; from osgeo  import ogr
    from gasp3.gt.prop.ff  import drv_name
    from gasp3.pyt.oss     import get_filename
    from gasp3.dt.to.geom  import create_point
    from gasp3.gt.prop.ext import get_ext
    
    extent = get_ext(inShp)
    
    # Create points of the new boundary based on the extent
    boundary_points = [
        create_point(extent[0], extent[3], api='ogr'),
        create_point(extent[1], extent[3], api='ogr'),
        create_point(extent[1], extent[2], api='ogr'),
        create_point(extent[0], extent[2], api='ogr'),
        create_point(extent[0], extent[3], api='ogr')
    ]
    
    # Get SRS for the output
    if not epsg:
        from gasp3.gt.prop.prj import get_shp_sref
        
        srs = get_shp_sref(inShp)
    
    else:
        from gasp3.gt.prop.prj import get_sref_from_epsg
        
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
    ring = ogr.Geometry(ogr.wkbLinearRing)
    
    for pnt in boundary_points:
        ring.AddPoint(pnt.GetX(), pnt.GetY())
    
    polygon = ogr.Geometry(ogr.wkbPolygon)
    polygon.AddGeometry(ring)
    
    feat.SetGeometry(polygon)
    lyr.CreateFeature(feat)
    
    feat.Destroy()
    shp.Destroy()
    
    return outShp


def pnts_to_boundary(pntShp, outBound, distMeters):
    """
    Create a boundary from Point using a tolerance in meters
    """
    
    from osgeo             import ogr
    from gasp3.pyt.oss     import get_filename
    from gasp3.gt.prop.ff  import drv_name
    from gasp3.dt.to.geom  import create_point
    from gasp3.gt.prop.prj import get_shp_sref
    
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
            create_point(X - distMeters, Y + distMeters, api='ogr'), # Topleft
            create_point(X + distMeters, Y + distMeters, api='ogr'), # TopRight
            create_point(X + distMeters, Y - distMeters, api='ogr'), # Lower Right
            create_point(X - distMeters, Y - distMeters, api='ogr'), # Lower Left
            create_point(X - distMeters, Y + distMeters, api='ogr')
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
    
    from gasp3.gt.prop.rst import rst_ext
    
    # Get Raster Extent
    left, right, bottom, top = rst_ext(inRst)
    
    # Get EPSG
    if not epsg:
        from gasp3.gt.prop.prj import get_rst_epsg
        
        epsg = get_rst_epsg(inRst)
    
    # Create Boundary
    return coords_to_boundary((left, top), (right, bottom), epsg, outShp)


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
        
        import os; from osgeo import gdal, ogr, osr
        from gasp3.gt.prop.ff import drv_name
        from gasp3.pyt.oss    import get_filename
        
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
        from gasp3 import exec_cmd
        
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
    
    from gasp3.dt.fm      import tbl_to_obj
    from gasp3.dt.to.geom import pnt_dfwxy_to_geodf
    from gasp3.dt.to.shp  import df_to_shp
    
    # XLS TO PANDAS DATAFRAME
    dataDf = tbl_to_obj(xlsFile, sheet=sheet)
    
    # DATAFRAME TO GEO DATAFRAME
    geoDataDf = pnt_dfwxy_to_geodf(dataDf, x_col, y_col, epsg)
    
    # GEODATAFRAME TO ESRI SHAPEFILE
    df_to_shp(geoDataDf, outShp)
    
    return outShp

