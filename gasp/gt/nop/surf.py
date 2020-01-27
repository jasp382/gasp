"""
Surface tools for Raster
"""

"""
Terrain
"""

def slope(demRst, slopeRst, data=None, api="pygrass"):
    """
    Get Slope Raster
    
    Data options:
    * percent;
    * degrees;
    """

    dataf = data if data == 'percent' or data == 'degrees' else 'degrees'

    if api == "pygrass":
        from grass.pygrass.modules import Module
    
        sl = Module(
            "r.slope.aspect", elevation=demRst, slope=slopeRst,
            format=dataf,
            overwrite=True, precision="FCELL", run_=False, quiet=True
        )
    
        sl()
    
    elif api == "grass":
        from gasp import exec_cmd
        
        rcmd = exec_cmd((
            "r.slope.aspect elevation={} slope={} format={} "
            "precision=FCELL --overwrite --quiet"
        ).format(demRst, slopeRst, dataf))
    
    else:
        raise ValueError("API {} is not available".format(api))
    
    return slopeRst


def aspect(dem, rst_aspect, from_north=None, api="pygrass"):
    """
    Generate Aspect Raster
    """

    aspect_tmp = rst_aspect if not from_north else rst_aspect + '_normal'

    expression = None if not from_north else (
        "if({r} == 0, -1, if({r} < 90, 90 - {r}, 450 - {r}))"
    ).format(r=aspect_tmp)

    if api == 'pygrass':
        from gass.pygrass.modules import Module

        m = Module(
            "r.slope", elevation=dem, aspect=aspect_tmp,
            overwrite=True, precision="FCELL", run_=False, quiet=True
        )

        m()
    
    elif api == 'grass':
        from gasp import exec_cmd

        rcmd = exec_cmd((
            "r.slope.aspect elevation={} aspect={} "
            "precision=FCELL --overwrite --quiet"
        ).format(dem, aspect_tmp))
    
    else:
        raise ValueError("API {} is not available".format(api))
    
    if from_north:
        from gasp.gt.nop.alg import rstcalc

        rrcmd = rstcalc(expression, rst_aspect, api=api)
    
    return rst_aspect


def gdal_slope(dem, srs, slope, unit='DEGREES'):
    """
    Create Slope Raster
    
    TODO: Test and see if is running correctly
    """
    
    import numpy;         import math
    from osgeo            import gdal
    from scipy.ndimage    import convolve
    from gasp.gt.fm.rst   import rst_to_array
    from gasp.gt.to.rst   import obj_to_rst
    from gasp.gt.prop.rst import get_cellsize, get_nodata
    
    # ################ #
    # Global Variables #
    # ################ #
    cellsize = get_cellsize(dem, gisApi='gdal')
    # Get Nodata Value
    NoData = get_nodata(dem, gisApi='gdal')
    
    # #################### #
    # Produce Slope Raster #
    # #################### #
    # Get Elevation array
    arr_dem = rst_to_array(dem)
    # We have to get a array with the number of nearst cells with values
    with_data = numpy.zeros((arr_dem.shape[0], arr_dem.shape[1]))
    numpy.place(with_data, arr_dem!=NoData, 1.0)
    mask = numpy.array([[1,1,1],
                        [1,0,1],
                        [1,1,1]])
    arr_neigh = convolve(with_data, mask, mode='constant')
    numpy.place(arr_dem, arr_dem==NoData, 0.0)
    # The rate of change in the x direction for the center cell e is:
    kernel_dz_dx_left = numpy.array([[0,0,1],
                                     [0,0,2],
                                     [0,0,1]])
    kernel_dz_dx_right = numpy.array([[1,0,0],
                                     [2,0,0],
                                     [1,0,0]])
    dz_dx = (convolve(arr_dem, kernel_dz_dx_left, mode='constant')-convolve(arr_dem, kernel_dz_dx_right, mode='constant')) / (arr_neigh * cellsize)
    # The rate of change in the y direction for cell e is:
    kernel_dz_dy_left = numpy.array([[0,0,0],
                                    [0,0,0],
                                    [1,2,1]])
    kernel_dz_dy_right = numpy.array([[1,2,1],
                                    [0,0,0],
                                    [0,0,0]])
    dz_dy = (convolve(arr_dem, kernel_dz_dy_left, mode='constant')-convolve(arr_dem, kernel_dz_dy_right, mode='constant')) / (arr_neigh * cellsize)
    # Taking the rate of change in the x and y direction, the slope for the center cell e is calculated using
    rise_run = ((dz_dx)**2 + (dz_dy)**2)**0.5
    if unit=='DEGREES':
        arr_slope = numpy.arctan(rise_run) * 57.29578
    elif unit =='PERCENT_RISE':
        arr_slope = numpy.tan(numpy.arctan(rise_run)) * 100.0
    # Estimate the slope for the cells with less than 8 neigh
    aux_dem = rst_to_array(dem)
    index_vizinhos = numpy.where(arr_neigh<8)
    for idx in range(len(index_vizinhos[0])):
        # Get Value of the cell
        lnh = index_vizinhos[0][idx]
        col = index_vizinhos[1][idx]
        e = aux_dem[lnh][col]
        a = aux_dem[lnh-1][col-1]
        if a == NoData:
            a = e
        if lnh==0 or col==0:
            a=e
        b = aux_dem[lnh-1][col]
        if b == NoData:
            b = e
        if lnh==0:
            b=e
        try:
            c = aux_dem[lnh-1][col+1]
            if c == NoData:
                c=e
            if lnh==0:
                c=e
        except:
            c = e
        d = aux_dem[lnh][col-1]
        if d == NoData:
            d = e
        if col==0:
            d=e
        try:
            f = aux_dem[lnh][col+1]
            if f == NoData:
                f=e
        except:
            f=e
        try:
            g = aux_dem[lnh+1][col-1]
            if g == NoData:
                g=e
            if col==0:
                g=e
        except:
            g=e
        try:
            h = aux_dem[lnh+1][col]
            if h ==NoData:
                h = e
        except:
            h=e
        try:
            i = aux_dem[lnh+1][col+1]
            if i == NoData:
                i = e
        except:
            i=e
        dz_dx = ((c + 2*f + i) - (a + 2*d + g)) / (8 * cellsize)
        dz_dy = ((g + 2*h + i) - (a + 2*b + c)) / (8 * cellsize)
        rise_sun = ((dz_dx)**2 + (dz_dy)**2)**0.5
        if unit == 'DEGREES':
            arr_slope[lnh][col] = math.atan(rise_sun) * 57.29578
        elif unit == 'PERCENT_RISE':
            arr_slope[lnh][col] = math.tan(math.atan(rise_sun)) * 100.0
    # Del value originally nodata
    numpy.place(arr_slope, aux_dem==NoData, numpy.nan)
    #arr_slope[lnh][col] = slope_degres
    obj_to_rst(arr_slope, slope, dem)


def viewshed(demrst, obsShp, output):
    """
    This tool computes a visibility analysis using observer points from
    a point shapefile.
    """
    
    import os;from gasp import exec_cmd
    from gasp.pyt.oss   import get_filename
    from gasp.gt.to.rst import saga_to_tif
    
    SAGA_RASTER = os.path.join(
        os.path.dirname(output),
        "sg_{}.sgrd".format(get_filename(output))
    )
    
    cmd = (
       "saga_cmd ta_lighting 6 -ELEVATION {elv} -POINTS {pnt} "
       "-VISIBILITY {out} -METHOD 0"
    ).format(
        elv=demrst, pnt=obsShp, out=SAGA_RASTER
    )
    
    outcmd = exec_cmd(cmd)
    
    # Convert to Tiif
    saga_to_tif(SAGA_RASTER, output)
    
    return output


def grs_viewshed(dem, obsPnt, outRst):
    """
    Compute viewshed
    """
    
    from grass.pygrass.modules import Module
    
    vshd = Module(
        "r.viewshed", input=dem, output=outRst, coordinates="east,north",
        flags="b", overwrite=True, run_=False, quiet=True
    )
    
    vshd()
    
    return outRst

