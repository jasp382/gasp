"""
Tools for sampling
"""

"""
Fishnets
"""
def create_fishnet(boundary, shpfishnet, x, y, xy_row_col=None, srs=None):
    """
    Create a Fishnet
    """
    
    import os
    from gasp.gt.prop.ext import get_ext
    from gasp.gt.prop.prj import get_epsg
    from gasp.g.smp       import fishnet

    # Check Path
    if not os.path.exists(os.path.dirname(shpfishnet)):
        raise ValueError('The path for the output doesn\'t exist')
    
    # Get boundary extent
    xmin, xmax, ymin, ymax = get_ext(boundary)
    # Get SRS
    epsg = get_epsg(boundary) if not srs else int(srs)
    
    return fishnet(
        (xmin, ymax), (xmax, ymin),
        shpfishnet, x, y, xy_row_col=xy_row_col, epsg=epsg
    )


def nfishnet_fm_rst(rst, max_row, max_col, out_fld):
    """
    Create N fishnets for the extent of one raster file
    the number of fishnets (N) will be determined by the extent of the raster
    and values max_row/max_col

    Fishnet cellsize will be the same as the raster
    """

    import os
    from osgeo           import gdal
    from gasp.g.prop.img import get_cell_size, rst_epsg
    from gasp.g.smp      import fishnet

    # Open Raster
    img = gdal.Open(rst)

    # Get EPSG
    epsg = rst_epsg(img)

    # Get Cellsize
    tl_x, cs_x, xr, tl_y, yr, cs_y = img.GetGeoTransform()

    # Get N cols and Rows
    numimg = img.ReadAsArray()
    nrows = numimg.shape[0]
    ncols = numimg.shape[1]

    # Get raster max_x and min_y
    rst_max_x = tl_x + (ncols * cs_x)
    rst_min_y = tl_y + (nrows * cs_y)

    # Fishnet N
    fnrows = int(nrows / max_row)
    fnrows = fnrows if fnrows == nrows / max_row else fnrows + 1
    fncols = int(ncols / max_col)
    fncols = fncols if fncols == ncols / max_col else fncols + 1

    fi = 1
    fishp = []
    for i in range(fnrows):
        # TopLeft Y
        tly = tl_y + ((max_row * cs_y) * i)

        # BottomRight Y
        bry = tly + (cs_y * max_row)
        # If fishnet min y is lesser than raster min_y
        # Use raster min_y

        if bry < rst_min_y:
            bry = rst_min_y
        
        for e in range(fncols):
            # TopLeft X 
            tlx = tl_x + ((max_col * cs_x) * e)

            # BottomRight X
            brx = tlx + (cs_x * max_col)

            # If fishnet max x is greater than raster max_x
            # Use raster max_x
            if brx > rst_max_x:
                brx = rst_max_x
            
            # Create fishnet file
            fshp = fishnet(
                (tlx, tly), (brx, bry),
                os.path.join(out_fld, 'fishnet_{}.shp'.format(str(fi))),
                cs_x, abs(cs_y), epsg=epsg
            )

            fishp.append(fshp)

            fi += 1

    return fishp


"""
Random Points
"""

def get_random_point(minX, maxX, minY, maxY):
    """
    Create a Single Random Point
    """
    
    import random
    from gasp.g.to import new_pnt
    
    x = minX + (random.random() * (maxX - minX))
    y = minY + (random.random() * (maxY - minY))
    
    pnt = new_pnt(x, y)
    
    return pnt


def create_random_points(inShp, nPoints, outShp, gisApi='pygrass'):
    """
    Generate Random Points Feature Class
    """
    
    if gisApi == 'pygrass':
        from grass.pygrass.modules import Module
        
        aleatorio = Module(
            "v.random", output=outShp, npoints=nPoints,
            restrict=inShp, overwrite=True, run_=False
        )
        aleatorio()
    
    elif gisApi == 'ogr':
        from osgeo            import ogr
        from gasp.gt.prop.ff  import drv_name
        from gasp.gt.prop.ext import get_ext
        
        # Get extent
        left, right, bottom, top = get_extent(inShp)
        
        # To be Continued
        """
        ausences = []
        shp = ogr.GetDriverByName(GDAL_GetDriverName(all_sample)).Open(all_sample, 0)
        lyr = shp.GetLayer()
        for i in range(number):
            equal = -1
            while equal != 0:
                random_pnt = CreateRandomPoint(extension['min_x'], extension['max_x'], extension['min_y'], extension['max_y'])
                equal = 0
                for feat in lyr:
                    geom = feat.GetGeometryRef()
                    geom_wkt = geom.ExportToWkt()
                    coord_geom = re.findall(r"[-+]?\d*\.\d+|\d+", geom_wkt)
                    dist = float(abs(
                        ((float(coord_geom[0]) - float(random_pnt[0]))**2 + (float(coord_geom[1]) - float(random_pnt[1]))**2)**0.5 
                    ))
                    if dist < 10.0:
                        equal += 1
            ausences.append(random_pnt)
        return ausences
        """
    return saida


def sample_to_points(points, col_name, rst):
    """
    v.what.rast - Uploads raster values at positions of vector
    points to the table.
    """
    
    from grass.pygrass.modules import Module
    
    m = Module(
        "v.what.rast", map=points, raster=rst,
        column=col_name,
        overwrite=True, run_=False, quiet=True
    )
    
    m()


def rst_random_pnt(rst, npnt, outvec):
    """
    Creates a raster map layer and vector point map containing
    randomly located points.
    """
    
    from grass.pygrass.modules import Module

    m = Module(
        "r.random", input=rst, npoints=npnt, vector=outvec,
        overwrite=True, run_=False, quiet=True
    ); m()
    
    return outVect


"""
Get values for sample from raster
"""

def pnt_val_on_rst(pntX, pntY, raster, geotransform=None,
                               rstShape=None):
    """
    Extract, for a given point, the value of a cell with the same location
    """
    
    import os
    import numpy
    from osgeo import gdal
    
    if type(raster) == str:
        if os.path.isfile(raster):
            img = gdal.Open(raster)
            geo_transform = img.GetGeoTransform()
            band = img.GetRasterBand(1)
        
            if not rstShape:
                tmpArray = numpy.array(band.ReadAsArray())
                nrLnh, nrCols = tmpArray.shape
        
            else:
                nrLnh, nrCols = rstShape
        
        else:
            raise ValueError('Raster is a string but not a file')
    
    else:
        geo_transform = geotransform if geotransform else None
        if not geo_transform:
            raise ValueError(
                'If raster is not a file, geotransform must be specified')
        
        if not rstShape:
            tmpArray = numpy.array(raster.ReadAsArray())
            nrLnh, nrCols = tmpArray.shape
        
        else:
            nrLnh, nrCols = rstShape
        
        band = raster
    
    px = int((pntX - geo_transform[0]) / geo_transform[1])
    py = int((pntY - geo_transform[3]) / geo_transform[5])
    
    if px < 0 or px > nrCols:
        return 0
    
    if py < 0 or py > nrLnh:
        return 0
    
    cell_value = band.ReadAsArray(px, py, 1, 1)
    
    cell_value = float(cell_value) if cell_value else None
    
    return cell_value


def gdal_valuesList_to_pointsList(raster, points_xy):
    import numpy
    from osgeo import gdal
    
    img = gdal.Open(raster)
    
    geo_transform = img.GetGeoTransform()
    band = img.GetRasterBand(1)
    
    array = numpy.array(band.ReadAsArray())
    lnh, col = array.shape
    
    values = []
    for pnt in points_xy:
        px = int((pnt[0] - geo_transform[0]) / geo_transform[1])
        
        if px < 0 or px > col:
            values.append(-9999)
            continue
        
        py = int((pnt[1] - geo_transform[3]) / geo_transform[5])
        if py < 0 or py > lnh:
            values.append(-9999)
            continue
        
        val = band.ReadAsArray(px, py, 1, 1)
        
        values.append(float(val))
    
    return values


def rst_val_to_points(pnt, rst):
    """
    Extract, for a given point dataset, the value of a cell with the same location
    
    Returns a dict:
    
    d = {
        fid: value,
        ...
    }
    """
    
    from osgeo           import ogr, gdal
    from gasp.gt.prop.ff import drv_name
    
    values_by_point = {}
    shp = ogr.GetDriverByName(drv_name(pnt)).Open(pnt, 0)
    lyr = shp.GetLayer()
    
    img = gdal.Open(rst)
    geo_transform = img.GetGeoTransform()
    band = img.GetRasterBand(1)
    
    for feat in lyr:
        geom = feat.GetGeometryRef()
        mx, my = geom.GetX(), geom.GetY()
        px = int((mx - geo_transform[0]) / geo_transform[1])
        py = int((my - geo_transform[3]) / geo_transform[5])
        
        val_pix = band.ReadAsArray(px, py, 1, 1)
        
        values_by_point[int(feat.GetFID())] = float(val_pix[0][0])
    
    return values_by_point


def rst_val_to_points2(pntShp, listRasters):
    """
    Pick raster value for each point in pntShp
    """
    
    from osgeo           import ogr
    from gasp.pyt        import obj_to_lst
    from gasp.gt.prop.ff import drv_name
    
    listRasters = obj_to_lst(listRasters)
    
    shp = ogr.GetDriverByName(
        drv_name(pntShp)).Open(pnt, 0)
    
    lyr = shp.GetLayer()
    
    pntDict = {}
    for feat in lyr:
        geom = feat.GetGeometryRef()
        
        x, y = geom.GetX(), geom.GetY()
        
        l = []
        for rst in listRasters:
            img = gdal.Open(rst)
            geo_transform = img.GetGeoTransform()
            band = img.GetRasterBand(1)
            
            px = int((x - geo_transform[0]) / geo_transform[1])
            py = int((y - geo_transform[3]) / geo_transform[5])
            value = band.ReadAsArray(px, py, 1, 1)
            
            l.append(list(value)[0])
            
            del img, geo_transform, band, px, py
        
        pntDict[feat.GetFID()] = l
    
    shp.Destroy()
    
    return pntDict


"""
Extract features from files
"""

def extract_random_features(inshp, nfeat, outshp, is_percentage=None):
    """
    Extract Random features from one Feature Class
    and save them in a new file
    """

    import numpy as np
    from gasp.gt.fmshp    import shp_to_obj
    from gasp.gt.toshp    import obj_to_shp
    from gasp.gt.prop.prj import get_epsg_shp

    # Open data
    df = shp_to_obj(inshp)

    # Get number of random features
    n = int(round(nfeat * df.shape[0] / 100, 0)) if is_percentage else nfeat

    # Get random sample
    df['idx'] = df.index
    rnd = np.random.choice(df.idx, n, replace=False)

    # Filter features
    rnd_df = df[df.idx.isin(rnd)]

    rnd_df.drop('idx', axis=1, inplace=True)

    # Save result
    epsg = get_epsg_shp(inshp)
    return obj_to_shp(rnd_df, 'geometry', epsg, outshp)
