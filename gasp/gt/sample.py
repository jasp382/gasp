"""
Tools for sampling
"""

"""
Fishnets
"""
def create_fishnet(boundary, fishnet, width=None, height=None, rowN=None, colN=None):
    """
    Create a Fishnet
    
    TODO doesn't work for Geographic SRS
    """
    
    import os; from osgeo import ogr
    from math             import ceil
    from gasp.pyt.oss     import fprop
    from gasp.gt.prop.ff  import drv_name
    from gasp.gt.prop.ext import get_ext
    from gasp.gt.prop.prj import get_srs
    
    # Get boundary extent
    xmin, xmax, ymin, ymax = get_ext(boundary)
    
    if width and height:
        # Clean width and height
        if type(width) != float:
            try:
                # Convert to float
                width = float(width)
            except:
                raise ValueError(
                    'Width value is not valid. Please give a numeric value'
                )
    
        if type(height) != float:
            try:
                # Convert to float
                height = float(height)
            except:
                raise ValueError(
                    'Height value is not valid. Please give a numeric value'
                )
    
        # get rows number
        rows = ceil((ymax-ymin) / height)
        # get columns number
        cols = ceil((xmax-xmin) / width)
    
    else:
        if rowN and colN:
            rows = int(rowN); cols = int(colN)
            width = ceil((xmax-xmin) / rows)
            height = ceil((ymax-ymin) / cols)
        
        else:
            raise ValueError(
                "You must specify the width and height of fishnet cells or "
                "instead the number of rows and cols of fishnet"
            )
    
    # Create output file
    if not os.path.exists(os.path.dirname(fishnet)):
        raise ValueError('The path for the output doesn\'t exist')
    
    out_fishnet = ogr.GetDriverByName(drv_name(
        fishnet)).CreateDataSource(fishnet)
    fishnet_lyr = out_fishnet.CreateLayer(
        str(fprop(fishnet, 'fn')), srs=get_srs(boundary),
        geom_type=ogr.wkbPolygon
    )
    
    feat_defn = fishnet_lyr.GetLayerDefn()
    
    # create grid cells
    # - start grid cell envelope -#
    ringXleftOrigin = xmin
    ringXrightOrigin = xmin + width
    ringYtopOrigin = ymax
    ringYbottomOrigin = ymax - height
    
    count_cols = 0
    while count_cols < cols:
        count_cols += 1
        
        # reset envelope for rows
        ringYtop = ringYtopOrigin
        ringYbottom = ringYbottomOrigin
        count_rows = 0
        
        while count_rows < rows:
            count_rows += 1
            
            ring = ogr.Geometry(ogr.wkbLinearRing)
            ring.AddPoint(ringXleftOrigin, ringYtop)
            ring.AddPoint(ringXrightOrigin, ringYtop)
            ring.AddPoint(ringXrightOrigin, ringYbottom)
            ring.AddPoint(ringXleftOrigin, ringYbottom)
            ring.AddPoint(ringXleftOrigin, ringYtop)
            poly = ogr.Geometry(ogr.wkbPolygon)
            poly.AddGeometry(ring)
            
            # add new geom to layer
            out_feature = ogr.Feature(feat_defn)
            out_feature.SetGeometry(poly)
            fishnet_lyr.CreateFeature(out_feature)
            out_feature = None
            
            # new envelope for next poly
            ringYtop = ringYtop - height
            ringYbottom = ringYbottom - height
        
        # new envelope for next poly
        ringXleftOrigin = ringXleftOrigin + width
        ringXrightOrigin = ringXrightOrigin + width
    
    out_fishnet.Destroy()
    
    return fishnet


def points_as_grid(boundary, fishnet_pnt, width=None, height=None,
                   nr_cols=None, nr_rows=None):
    """
    Equivalent to the centroid of each cell of a fishnet grid
    """
    
    import os; from osgeo import ogr
    from math             import ceil
    from gasp.pyt.oss     import fprop
    from gasp.gt.prop.ff  import drv_name
    from gasp.gt.prop.ext import get_ext
    from gasp.gt.prop.prj import get_shp_sref
    
    # Get boundary extent
    xmin, xmax, ymin, ymax = get_ext(boundary)
    
    # Clean width and height
    if width and height:
        if type(width) != float:
            try:
                # Convert to float
                width = float(width)
            except:
                raise ValueError(
                    'Width value is not valid. Please give a numeric value'
                )
        
        if type(height) != float:
            try:
                # Convert to float
                height = float(height)
            except:
                raise ValueError(
                    'Height value is not valid. Please give a numeric value'
                )
    
    else:
        if nr_cols and nr_rows:
            if type(nr_cols) != float:
                try:
                    # convert to float
                    nr_cols = float(nr_cols)
                except:
                    raise ValueError(
                        'Columns number value is not valid. Please give a numeric value'
                    )
            
            if type(nr_rows) != float:
                try:
                    nr_rows = float(nr_rows)
                except:
                    raise ValueError(
                        'Lines number value is not valid. Please give a numeric value'
                    )
            
            width = (xmax + xmin) / nr_cols
            height = (ymax + ymin) / nr_rows
        
        else:
            raise ValueError('Please giver numeric values to with/height or to nr_cols/nr_rows')
    
    # get rows number
    rows = ceil((ymax-ymin) / height)
    # get columns number
    cols = ceil((xmax-xmin) / width)
    
    # Create output file
    if not os.path.exists(os.path.dirname(fishnet_pnt)):
        return 'The path for the output doesn\'t exist'
    
    out_fishnet = ogr.GetDriverByName(drv_name(
        fishnet_pnt)).CreateDataSource(fishnet_pnt)
    fishnet_lyr = out_fishnet.CreateLayer(
        fprop(fishnet_pnt, 'fn'), get_shp_sref(boundary),
        geom_type=ogr.wkbPoint
    )
    
    feat_defn = fishnet_lyr.GetLayerDefn()
    
    # create grid cells
    # - start grid cell envelope -#
    ringXleftOrigin = xmin
    ringXrightOrigin = xmin + width
    ringYtopOrigin = ymax
    ringYbottomOrigin = ymax - height
    
    count_cols = 0
    while count_cols < cols:
        count_cols += 1
        
        # reset envelope for rows
        ringYtop = ringYtopOrigin
        ringYbottom = ringYbottomOrigin
        count_rows = 0
        
        while count_rows < rows:
            count_rows += 1
            
            pnt = ogr.Geometry(ogr.wkbPoint)
            pnt.AddPoint(
                (ringXleftOrigin + ringXrightOrigin) / 2.0,
                (ringYbottom + ringYtop) / 2.0
            )
            
            # add new geom to layer
            out_feature = ogr.Feature(feat_defn)
            out_feature.SetGeometry(pnt)
            fishnet_lyr.CreateFeature(out_feature)
            out_feature = None
            
            # new envelope for next poly
            ringYtop = ringYtop - height
            ringYbottom = ringYbottom - height
        
        # new envelope for next poly
        ringXleftOrigin = ringXleftOrigin + width
        ringXrightOrigin = ringXrightOrigin + width
    
    out_fishnet.Destroy()


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

