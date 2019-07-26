"""
Data to Raster File
"""

"""
Array to Raster
"""

def array_to_raster(inArray, outRst, template, noData=None):
    """
    Send Array to Raster
    
    API Available:
    * gdal;
    """
    
    gisApi = 'gdal'
    
    if gisApi == 'gdal':
        from osgeo             import gdal, osr, gdal_array
        from gasp3.gt.prop.ff  import drv_name
        from gasp3.gt.prop.prj import get_epsg_raster
        
        epsg = get_epsg_raster(template)
    
        img_template  = gdal.Open(template)
        geo_transform = img_template.GetGeoTransform()
        rows, cols    = inArray.shape
        driver        = gdal.GetDriverByName(drv_name(outRst))
        out           = driver.Create(
            outRst, cols, rows, 1,
            gdal_array.NumericTypeCodeToGDALTypeCode(inArray.dtype)
        )
        out.SetGeoTransform(geo_transform)
        outBand       = out.GetRasterBand(1)
    
        if noData:
            outBand.SetNoDataValue(noData)
        
        outBand.WriteArray(inArray)
    
        if epsg:
            from gasp3.gt.prop.prj import epsg_to_wkt
            srs = epsg_to_wkt(epsg)
            out.SetProjection(srs)
    
        outBand.FlushCache()
    
    else:
        raise ValueError('The api {} is not available'.format(gisApi))
    
    return outRst


"""
Conversion between formats
"""

def rst_to_grs(rst, grsRst, lmtExt=None, as_cmd=None):
    """
    Raster to GRASS GIS Raster
    """
    
    if not as_cmd:
        from grass.pygrass.modules import Module
        
        __flag = 'o' if not lmtExt else 'or'
        
        m = Module(
            "r.in.gdal", input=rst, output=grsRst, flags='o',
            overwrite=True, run_=False, quiet=True,
        )
        
        m()
    
    else:
        from gasp3 import exec_cmd
        
        rcmd = exec_cmd((
            "r.in.gdal input={} output={} -o{} --overwrite "
            "--quiet"
        ).format(rst, grsRst, "" if not lmtExt else " -r"))
    
    return grsRst


def grs_to_rst(grsRst, rst, as_cmd=None, allBands=None):
    """
    GRASS Raster to Raster
    """
    
    from gasp3.gt.prop.ff import grs_rst_drv
    from gasp3.pyt.oss    import get_fileformat
    
    rstDrv = grs_rst_drv()
    rstExt = get_fileformat(rst)
    
    if not as_cmd:
        from grass.pygrass.modules import Module
        
        m = Module(
            "r.out.gdal", input=grsRst, output=rst,
            format=rstDrv[rstExt], flags='c' if not allBands else '',
            createopt="INTERLEAVE=PIXEL,TFW=YES" if allBands else '',
            overwrite=True, run_=False, quiet=True
        )
        
        m()
    
    else:
        from gasp3 import exec_cmd
        
        rcmd = exec_cmd((
            "r.out.gdal input={} output={} format={} "
            "{} --overwrite --quiet"
        ).format(
            grsRst, rst, rstDrv[rstExt],
            "-c" if not allBands else "createopt=\"INTERLEAVE=PIXEL,TFW=YES\""
        ))
    
    return rst


def grs_to_mask(inRst):
    """
    Grass Raster to Mask
    """
    
    from grass.pygrass.modules import Module
    
    m = Module('r.mask', raster=inRst, quiet=True, run_=False)
    
    m()


def saga_to_tif(inFile, outFile):
    """
    SAGA GIS format to GeoTIFF
    """
    
    from gasp3         import exec_cmd
    from gasp3.pyt.oss import get_fileformat
    
    # Check if outFile is a GeoTiff
    if get_fileformat(outFile) != '.tif':
        raise ValueError(
            'Outfile should have GeoTiff format'
        )
    
    cmd = (
        "saga_cmd io_gdal 2 -GRIDS {} "
        "-FILE {}"
    ).format(inFile, outFile)
    
    outcmd = exec_cmd(cmd)
    
    return outFile


def tif_to_grid(inFile, outFile):
    """
    GeoTiff to SAGA GIS GRID
    """
    
    from gasp3 import exec_cmd
    
    comand = (
        "saga_cmd io_gdal 0 -FILES {} "
        "-GRIDS {}"
    ).format(inFile, outFile)
    
    outcmd = exec_cmd(comand)
    
    return outFile


"""
Feature Class to Raster
"""

def shp_to_rst(shp, inSource, cellsize, nodata, outRaster, epsg=None,
               rst_template=None, snapRst=None, api='gdal'):
    """
    Feature Class to Raster
    
    cellsize will be ignored if rst_template is defined
    
    * API's Available:
    - gdal;
    - pygrass;
    - grass;
    """
    
    if api == 'gdal':
        from osgeo            import gdal, ogr
        from gasp3.gt.prop.ff import drv_name
    
        if not epsg:
            from gasp3.gt.prop.prj import get_shp_sref
            srs = get_shp_sref(shp).ExportToWkt()
        else:
            from gasp3.gt.prop.prj import epsg_to_wkt
            srs = epsg_to_wkt(epsg)
    
        # Get Extent
        dtShp = ogr.GetDriverByName(
            drv_name(shp)).Open(shp, 0)
    
        lyr = dtShp.GetLayer()
    
        if not rst_template:
            if not snapRst:
                x_min, x_max, y_min, y_max = lyr.GetExtent()
                x_res = int((x_max - x_min) / cellsize)
                y_res = int((y_max - y_min) / cellsize)
            
            else:
                from gasp3.gt.prop.rst import adjust_ext_to_snap
                
                x_min, y_max, y_res, x_res, cellsize = adjust_ext_to_snap(
                    shp, snapRst
                )
    
        else:
            from gasp3.dt.fm.rst import rst_to_array
        
            img_temp = gdal.Open(rst_template)
            geo_transform = img_temp.GetGeoTransform()
        
            y_res, x_res = rst_to_array(rst_template).shape
    
        # Create output
        dtRst = gdal.GetDriverByName(drv_name(outRaster)).Create(
            outRaster, x_res, y_res, gdal.GDT_Byte
        )
    
        if not rst_template:
            dtRst.SetGeoTransform((x_min, cellsize, 0, y_max, 0, -cellsize))
    
        else:
            dtRst.SetGeoTransform(geo_transform)
        
        dtRst.SetProjection(str(srs))
    
        bnd = dtRst.GetRasterBand(1)
        bnd.SetNoDataValue(nodata)
    
        gdal.RasterizeLayer(dtRst, [1], lyr, burn_values=[1])
    
        del lyr
        dtShp.Destroy()
    
    elif api == 'grass' or api == 'pygrass':
        """
        Vectorial geometry to raster
    
        If source is None, the convertion will be based on the cat field.
    
        If source is a string, the convertion will be based on the field
        with a name equal to the given string.
    
        If source is a numeric value, all cells of the output raster will have
        that same value.
        """
        
        __USE = "cat" if not inSource else "attr" if type(inSource) == str \
            else "val" if type(inSource) == int or \
            type(inSource) == float else None
        
        if not __USE:
            raise ValueError('\'source\' parameter value is not valid')
        
        if api == 'pygrass':
            from grass.pygrass.modules import Module
            
            m = Module(
                "v.to.rast", input=shp, output=outRaster, use=__USE,
                attribute_column=inSource if __USE == "attr" else None,
                value=inSource if __USE == "val" else None,
                overwrite=True, run_=False, quiet=True
            )
            
            m()
        
        else:
            from gasp3 import exec_cmd
            
            rcmd = exec_cmd((
                "v.to.rast input={} output={} use={}{} "
                "--overwrite --quiet"
            ).format(
                shp, outRaster, __USE,
                "" if __USE == "cat" else " attribute_column={}".format(inSource) \
                    if __USE == "attr" else " val={}".format(inSource)
            ))
    
    else:
        raise ValueError('API {} is not available'.format(api))
    
    return outRaster

