"""
Run Informative Value Method in different Software
"""


def infovalue(landslides, variables, iv_rst, dataEpsg):
    """
    Informative Value using GDAL Library
    """
    
    import os; import math; import numpy
    from osgeo              import gdal
    from gasp3.dt.fm.rst    import rst_to_array
    from gasp3.dt.fm        import tbl_to_obj
    from gasp3.gt.prop.feat import get_gtype
    from gasp3.gt.prop.rst  import rst_shape
    from gasp3.gt.prop.rst  import count_cells
    from gasp3.gt.prop.rst  import get_cellsize
    from gasp3.gt.prop.rst  import frequencies
    from gasp3.pyt.oss      import create_folder
    from gasp3.dt.to.rst    import array_to_raster
    
    # Create Workspace for temporary files
    workspace = create_folder(os.path.join(
        os.path.dirname(landslides), 'tmp')
    )
    
    # Get Variables Raster Shape and see if there is any difference
    varShapes = rst_shape(variables)
    for i in range(1, len(variables)):
        if varShapes[variables[i-1]] != varShapes[variables[i]]:
            raise ValueError((
                'All rasters must have the same dimension! '
                'Raster {} and Raster {} have not the same shape!'
            ).format(variables[i-1], variables[i]))
    
    # See if landslides are raster or not
    # Try to open as raster
    try:
        land_rst = rst_to_array(landslides)
        lrows, lcols = land_rst.shape
        
        if [lrows, lcols] != varShapes[variables[0]]:
            raise ValueError((
                "Raster with Landslides ({}) has to have the same "
                "dimension that Raster Variables"
            ).format(landslides))
    
    except:
        # Landslides are not Raster
        # Open as Feature Class
        # See if is Point or Polygon
        land_df  = tbl_to_obj(landslides)
        geomType = get_gtype(land_df, geomCol="geometry", gisApi='pandas')
        
        if geomType == 'Polygon' or geomType == 'MultiPolygon':
            # it will be converted to raster bellow
            land_poly = landslides
        
        elif geomType == 'Point' or geomType == 'MultiPoint':
            # Do a Buffer
            from gasp3.gt.anls.prox.bf import geodf_buffer_to_shp
            
            land_poly = geodf_buffer_to_shp(land_df, 100, os.path.join(
                workspace, 'landslides_buffer.shp'
            ))
        
        # Convert To Raster
        from gasp3.dt.to.rst import shp_to_rst
        
        land_raster = shp_to_rst(
            land_poly, None, get_cellsize(variables[0], gisApi='gdal'), -9999,
            os.path.join(workspace, 'landslides_rst.tif'),
            rst_template=variables[0], api='gdal'
        )
        
        land_rst = rst_to_array(land_raster)
    
    # Get Number of cells of each raster and number of cells
    # with landslides
    landsldCells = frequencies(land_raster)[1]
    totalCells   = count_cells(variables[0])
    
    # Get number of cells by classe in variable
    freqVar = { r : frequencies(r) for r in variables }
    
    for rst in freqVar:
        for cls in freqVar[rst]:
            if cls == 0:
                freqVar[rst][-1] = freqVar[rst][cls]
                del freqVar[rst][cls]
            
            else:
                continue
    
    # Get cell number with landslides by class
    varArray = { r : rst_to_array(r) for r in variables }
    
    for r in varArray:
        numpy.place(varArray[r], varArray[r]==0, -1)
    
    landArray  = { r : land_rst * varArray[r] for r in varArray }
    freqLndVar = { r : frequencies(landArray[r]) for r in landArray }
    
    # Estimate VI for each class on every variable
    vi = {}
    for var in freqVar:
        vi[var] = {}
        for cls in freqVar[var]:
            if cls in freqLndVar[var]:
                vi[var][cls] = math.log10(
                    (float(freqLndVar[var][cls]) / freqVar[var][cls]) / (
                        float(landsldCells) / totalCells)
                )
            
            else:
                vi[var][cls] = 9999
    
    # Replace Classes without VI, from 9999 to minimum VI
    vis = []
    for d in vi.values():
        vis += d.values()
    
    min_vi = min(vis)
    
    for r in vi:
        for cls in vi[r]:
            if vi[r][cls] == 9999:
                vi[r][cls] = min_vi
            else:
                continue
    
    # Replace cls by vi in rst_arrays
    resultArrays = {v : numpy.zeros(varArray[v].shape) for v in varArray}
    for v in varArray:
        numpy.place(resultArrays[v], resultArrays[v] == 0, -128)
    
    for v in varArray:
        for cls in vi[v]:
            numpy.place(resultArrays[v], varArray[v]==cls, vi[v][cls])
    
    # Sum all arrays and save the result as raster
    vi_rst = resultArrays[variables[0]] + resultArrays[variables[1]]
    for v in range(2, len(variables)):
        vi_rst = vi_rst + resultArrays[variables[v]]
    
    numpy.place(vi_rst, vi_rst == len(variables) * -128, -128)
    
    result = array_to_raster(
        vi_rst, iv_rst, variables[i], dataEpsg,
        gdal.GDT_Float32, noData=-128, gisApi='gdal'
    )
    
    return iv_rst

