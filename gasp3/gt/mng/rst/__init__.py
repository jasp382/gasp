"""
Raster Management Tools
"""

def rst_rotation(inFolder, template, outFolder, img_format='.tif'):
    """
    Invert raster data
    """
    
    import os; from osgeo  import gdal
    from gasp3.pyt.oss     import list_files
    from gasp3.dt.fm.rst   import rst_to_array
    from gasp3.gt.prop.rst import get_nodata
    from gasp3.dt.to.rst   import array_to_raster
    
    rasters = list_files(inFolder, file_format=img_format)
    
    for rst in rasters:
        a  = rst_to_array(rst)
        nd = get_nodata(rst, gisApi='gdal')
        
        array_to_raster(
            a[::-1],
            os.path.join(outFolder, os.path.basename(rst)),
            template, None, gdal.GDT_Float32, noData=nd,
            gisApi='gdal'
        )

"""
Join Bands
"""

def comp_bnds(rsts, outRst):
    """
    Composite Bands
    """
    
    from osgeo             import gdal, gdal_array
    from gasp3.dt.fm.rst   import rst_to_array
    from gasp3.gt.prop.ff  import drv_name
    from gasp3.gt.prop.rst import get_nodata
    from gasp3.gt.prop.prj import get_rst_epsg, epsg_to_wkt
    
    # Get Arrays
    _as = [rst_to_array(r) for r in rsts]
    
    # Get nodata values
    nds = [get_nodata(r) for r in rsts]
    
    # Assume that first raster is the template
    img_temp = gdal.Open(rsts[0])
    geo_tran = img_temp.GetGeoTransform()
    band = img_temp.GetRasterBand(1)
    dataType = gdal_array.NumericTypeCodeToGDALTypeCode(_as[0].dtype)
    rows, cols = _as[0].shape
    epsg = get_rst_epsg(rsts[0])
    
    # Create Output
    drv = gdal.GetDriverByName(drv_name(outRst))
    out = drv.Create(outRst, cols, rows, len(_as), dataType)
    out.SetGeoTransform(geo_tran)
    out.SetProjection(epsg_to_wkt(epsg))
    
    # Write all bands
    for i in range(len(_as)):
        outBand = out.GetRasterBand(i+1)
        outBand.SetNoDataValue(nds[i])
        outBand.WriteArray(_as[i])
        
        outBand.FlushCache()
    
    return outRst

"""
Clipping
"""

def clip_rst(raster, clipShp, outRst, nodataValue=None, api='gdal'):
    """
    Clip Raster using GDAL WARP
    """
    
    if api == 'gdal':
        from gasp3            import exec_cmd
        from gasp3.gt.prop.ff import drv_name
    
        outcmd = exec_cmd((
            "gdalwarp {ndata}-cutline {clipshp} -crop_to_cutline "
            "-of {ext} {inraster} -overwrite {outrst}"
        ).format(
            clipshp=clipShp, inraster=raster, outrst=outRst,
            ext=drv_name(outRst),
            ndata="-dstnodata {} ".format(
                str(nodataValue)) if nodataValue else ""
        ))
    
    elif api == 'pygrass':
        from grass.pygrass.modules import Module
        
        m = Module(
            'r.clip', input=raster, output=outRst,
            overwrite=True, run_=False, quiet=True
        )
        
        m()
    
    elif api == 'grass':
        from gasp3 import exec_cmd
        
        rcmd = exec_cmd('r.clip input={} output={} --overwrite --quiet'.format(
            raster, outRst
        ))
    
    else:
        raise ValueError('API {} is not available'.format(api))
    
    return outRst


"""
Merge and Combine raster dataset
"""
def mosaic_raster(inRasterS, o, asCmd=None):
    """
    The GRASS program r.patch allows the user to build a new raster map the size
    and resolution of the current region by assigning known data values from
    input raster maps to the cells in this region. This is done by filling in
    "no data" cells, those that do not yet contain data, contain NULL data, or,
    optionally contain 0 data, with the data from the first input map.
    Once this is done the remaining holes are filled in by the next input map,
    and so on. This program is useful for making a composite raster map layer
    from two or more adjacent map layers, for filling in "holes" in a raster map
    layer's data (e.g., in digital elevation data), or for updating an older map
    layer with more recent data. The current geographic region definition and
    mask settings are respected.
    The first name listed in the string input=name,name,name, ... is the name of
    the first map whose data values will be used to fill in "no data" cells in
    the current region. The second through last input name maps will be used,
    in order, to supply data values for for the remaining "no data" cells.
    """
    
    if not asCmd:
        from grass.pygrass.modules import Module
    
        m = Module(
            "r.patch", input=inRasterS, output=o,
            overwrite=True, run_=False, quiet=True
        )
    
        m()
    
    else:
        from gasp3 import exec_cmd
        
        rcmd = exec_cmd("r.patch input={} output={} --overwrite --quiet".format(
            ",".join(inRasterS), o
        ))
    
    return o


def sat_bnds_to_mosaic(bands, outdata, epsg, ref_raster, loc=None):
    """
    Satellite image To mosaic
    
    bands = {
        'bnd_2' : [path_to_file, path_to_file],
        'bnd_3' : [path_to_file, path_to_file],
        'bnd_4' : [path_to_file, path_to_file],
    }
    """
    
    """
    Start GRASS GIS Session
    """
    
    import os
    from gasp3.pyt.oss     import get_filename
    from gasp3.gt.wenv.grs import run_grass
    
    grass_base = run_grass(
        outdata, grassBIN='grass77',
        location=loc if loc else 'gr_loc', srs=epsg
    )
    
    import grass.script as grass
    import grass.script.setup as gsetup
    
    gsetup.init(grass_base, outdata, loc if loc else 'gr_loc', 'PERMANENT')
    
    # ************************************************************************ #
    # GRASS MODULES #
    # ************************************************************************ #
    from gasp3.dt.to.rst   import rst_to_grs, grs_to_rst
    from gasp3.gt.wenv.grs import rst_to_region
    # ************************************************************************ #
    # SET GRASS GIS LOCATION EXTENT #
    # ************************************************************************ #
    extRst = rst_to_grs(ref_raster, 'extent_raster')
    rst_to_region(extRst)
    # ************************************************************************ #
    # SEND DATA TO GRASS GIS #
    # ************************************************************************ #
    grsBnds = {}
    
    for bnd in bands:
        l= []
        for b in bands[bnd]:
            bb = rst_to_grs(b, get_filename(b))
            l.append(bb)
        
        grsBnds[bnd] = 1
    # ************************************************************************ #
    # PATCH bands and export #
    # ************************************************************************ #
    for bnd in grsBnds:
        mosaic_band = mosaic_raster(grsBnds[bnd], bnd)
        
        grsBnds[bnd] = grs_to_rst(mosaic_band, os.path.join(
            outdata, mosaic_band + '.tif'
        ), as_cmd=True)
    
    return grsBnds

