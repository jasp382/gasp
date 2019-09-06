"""
Resample Raster Files
"""

def match_cellsize_and_clip(rstBands, refRaster, outFolder,
                            clipShp=None):
    """
    Resample images to make them with the same resolution and clip
    
    Good to resample Sentinel bands with more than 10 meters.
    
    Dependencies: 
    * GRASS GIS;
    * GDAL/OGR.
    """
    
    import os
    from gasp3.gt.prop.prj import get_rst_epsg
    from gasp3.gt.wenv.grs import run_grass
    from gasp3.pyt.oss     import get_filename, create_folder
    
    # Check if outfolder exists
    if not os.path.exists(outFolder):
        create_folder(outFolder, overwrite=None)
    
    # Get EPSG from refRaster
    epsg = get_rst_epsg(refRaster, returnIsProj=None)
    
    """
    Start GRASS GIS Session
    """
    GRS_WORKSPACE = create_folder(os.path.join(outFolder, 'grswork'))
    grsb = run_grass(
        GRS_WORKSPACE, grassBIN='grass77', location='resample',
        srs=epsg
    )
    
    import grass.script as grass
    import grass.script.setup as gsetup
    
    gsetup.init(grsb, GRS_WORKSPACE, 'resample', 'PERMANENT')
    
    """
    Import packages related with GRASS GIS
    """
    from gasp3.dt.to.rst   import rst_to_grs, grs_to_rst
    from gasp3.gt.wenv.grs import rst_to_region
    from gasp3.dt.to.shp   import shp_to_grs
    from gasp3.dt.to.rst   import shp_to_rst, grs_to_mask
    
    # Send Ref Raster to GRASS GIS and set region
    extRst = rst_to_grs(refRaster, 'ext_rst')
    rst_to_region(extRst)
    
    # Import all bands in rstBands
    newBands = []
    for i in rstBands:
        newBands.append(rst_to_grs(i, get_filename(i)))
    
    # Export bands
    bndFile = []
    outf = GRS_WORKSPACE if clipShp else outFolder
    for i in newBands:
        bndFile.append(grs_to_rst(i, os.path.join(outf, i + '.tif')))
    
    if clipShp:
        """
        Clip shape to raster
        """
        
        rstClip = shp_to_rst(
            clipShp, None, None, 0, os.path.join(
                GRS_WORKSPACE, 'clip_ref_raster.tif'
            ), snapRst=refRaster, api='gdal'
        )
        
        """
        Clip Bands
        """
        
        grsb = run_grass(
            GRS_WORKSPACE, grassBIN='grass77',
            location='clip_bnds', srs=epsg
        )
        
        import grass.script as grass
        import grass.script.setup as gsetup
        
        gsetup.init(grsb, GRS_WORKSPACE, 'clip_bnds', 'PERMANENT')
        
        extRst = rst_to_grs(rstClip, 'clip_ref_raster', lmtExt=None, as_cmd=True)
        rst_to_region(extRst)
        
        for i in bndFile:
            a = rst_to_grs(i, get_filename(i), lmtExt=True, as_cmd=True)
            grs_to_rst(a, os.path.join(outFolder, a + '.tif'))
    
    return outFolder

