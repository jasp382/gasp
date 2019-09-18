"""
Terrain Modelling Tools
"""


def make_DEM(grass_workspace, data, field, output, extent_template,
             method="IDW"):
    """
    Create Digital Elevation Model
    
    Methods Available:
    * IDW;
    * BSPLINE;
    * SPLINE;
    * CONTOUR
    """
    
    from gasp3.pyt.oss     import get_filename
    from gasp3.gt.wenv.grs import run_grass
    from gasp3.gt.prop.prj import get_rst_epsg
    
    LOC_NAME = get_filename(data, forceLower=True)[:5] + "_loc"
    
    # Get EPSG From Raster
    EPSG = get_rst_epsg(extent_template)
    
    # Create GRASS GIS Location
    grass_base = run_grass(grass_workspace, location=LOC_NAME, srs=EPSG)
    
    # Start GRASS GIS Session
    import grass.script as grass
    import grass.script.setup as gsetup
    gsetup.init(grass_base, grass_workspace, LOC_NAME, 'PERMANENT')
    
    # IMPORT GRASS GIS MODULES #
    from gasp3.gt.to.rst   import rst_to_grs, grs_to_rst
    from gasp3.gt.to.shp   import shp_to_grs
    from gasp3.gt.wenv.grs import rst_to_region
    
    # Configure region
    rst_to_grs(extent_template, 'extent')
    rst_to_region('extent')
    
    # Convert elevation "data" to GRASS Vector
    elv = shp_to_grs(data, 'elevation')
    
    OUTPUT_NAME = get_filename(output, forceLower=True)
    
    if method == "BSPLINE":
        # Convert to points
        from gasp3.gt.mng.feat      import feat_vertex_to_pnt
        from gasp3.gt.spnlst.interp import bspline
        
        elev_pnt = feat_vertex_to_pnt(elv, "elev_pnt", nodes=None)
        
        outRst = bspline(elev_pnt, field, OUTPUT_NAME, lyrN=1, asCMD=True)
    
    elif method == "SPLINE":
        # Convert to points
        from gasp3.gt.mng.feat      import feat_vertex_to_pnt
        from gasp3.gt.spnlst.interp import surfrst
        
        elev_pnt = feat_vertex_to_pnt(elv, "elev_pnt", nodes=None)
        
        outRst = surfrst(elev_pnt, field, OUTPUT_NAME, lyrN=1, ascmd=True)
    
    elif method == "CONTOUR":
        from gasp3.gt.to.rst        import shp_to_rst
        from gasp3.gt.spnlst.interp import surfcontour
        
        # Elevation (GRASS Vector) to Raster
        elevRst = shp_to_rst(
            elv, field, None, None, 'rst_elevation', api="pygrass")
        
        # Run Interpolator
        outRst = surfcontour(elevRst, OUTPUT_NAME, ascmd=True)
    
    elif method == "IDW":
        from gasp3.gt.spnlst.interp import ridw
        from gasp3.gt.spanlst.alg   import rstcalc
        from gasp3.gt.to.rst        import shp_to_rst
        
        # Elevation (GRASS Vector) to Raster
        elevRst = shp_to_rst(
            elv, field, None, None, 'rst_elevation', api='pygrass')
        # Multiply cells values by 100 000.0
        rstcalc('int(rst_elevation * 100000)', 'rst_elev_int', api='pygrass')
        # Run IDW to generate the new DEM
        ridw('rst_elev_int', 'dem_int', numberPoints=15)
        # DEM to Float
        rstcalc('dem_int / 100000.0', OUTPUT_NAME, api='pygrass')
    
    # Export DEM to a file outside GRASS Workspace
    grs_to_rst(OUTPUT_NAME, output)
    
    return output

