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


def sqlite_to_shp(db, table, out, where=None, notTable=None,
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

def rstext_to_shp(inRst, outShp, epsg=None):
    """
    Raster Extent to Feature Class
    """
    
    from gasp3.gt.prop.rst import rst_ext
    
    # Get Raster Extent
    left, right, bottom, top = rst_ext(inRst)
    
    # Get EPSG
    if not epsg:
        from gasp3.gt.prop.prj import get_epsg_raster
        
        epsg = get_epsg_raster(inRst)
    
    # Create Boundary
    return coords_to_boundary((left, top), (right, bottom), epsg, outShp)

