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
    from gasp.gt.prop.prj import get_rst_epsg
    from gasp.gt.wenv.grs import run_grass
    from gasp.pyt.oss     import fprop, mkdir
    
    # Check if outfolder exists
    if not os.path.exists(outFolder):
        mkdir(outFolder, overwrite=None)
    
    # Get EPSG from refRaster
    epsg = get_rst_epsg(refRaster, returnIsProj=None)
    
    """
    Start GRASS GIS Session
    """
    GRS_WORKSPACE = mkdir(os.path.join(outFolder, 'grswork'))
    grsb = run_grass(
        GRS_WORKSPACE, grassBIN='grass78', location='resample',
        srs=epsg
    )
    
    import grass.script as grass
    import grass.script.setup as gsetup
    
    gsetup.init(grsb, GRS_WORKSPACE, 'resample', 'PERMANENT')
    
    """
    Import packages related with GRASS GIS
    """
    from gasp.gt.torst    import rst_to_grs, grs_to_rst
    from gasp.gt.wenv.grs  import rst_to_region
    from gasp.gt.toshp.cff import shp_to_grs
    from gasp.gt.torst    import shp_to_rst, grs_to_mask
    
    # Send Ref Raster to GRASS GIS and set region
    extRst = rst_to_grs(refRaster, 'ext_rst')
    rst_to_region(extRst)
    
    # Import all bands in rstBands
    newBands = []
    for i in rstBands:
        newBands.append(rst_to_grs(i, fprop(i, 'fn')))
    
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
            GRS_WORKSPACE, grassBIN='grass78',
            location='clip_bnds', srs=epsg
        )
        
        import grass.script as grass
        import grass.script.setup as gsetup
        
        gsetup.init(grsb, GRS_WORKSPACE, 'clip_bnds', 'PERMANENT')
        
        extRst = rst_to_grs(rstClip, 'clip_ref_raster', lmtExt=None, as_cmd=True)
        rst_to_region(extRst)
        
        for i in bndFile:
            a = rst_to_grs(i, fprop(i, 'fn'), lmtExt=True, as_cmd=True)
            grs_to_rst(a, os.path.join(outFolder, a + '.tif'))
    
    return outFolder


def resample_by_majority(refrst, valrst, out_rst):
    """
    Resample valrst based on refrst:
        Get Majority value of valrst for each cell in refrst

    Useful when ref raster has cellsize greater
    than value raster.

    TODO: Valrst must be of int type
    """

    import numpy         as np
    from osgeo           import gdal
    from gasp.g.prop.img import get_cell_size, get_nd
    from gasp.gt.torst   import obj_to_rst

    # Data to Array
    if type(refrst) == gdal.Dataset:
        refsrc = refrst
    
    else:
        refsrc = gdal.Open(refrst)
    
    if type(valrst) == gdal.Dataset:
        valsrc = valrst
    else:
        valsrc = gdal.Open(valrst)

    refnum = refsrc.ReadAsArray()
    valnum = valsrc.ReadAsArray()

    # Get Ref shape
    ref_shape = refnum.shape

    # in a row, how many cells valnum are for each refnum cell
    refcs = int(get_cell_size(refsrc)[0])
    valcs = int(get_cell_size(valsrc)[0])
    dcell = int(refcs / valcs)

    # Valnum must be of int type

    # Create generalized/resampled raster
    resnum = np.zeros(ref_shape, dtype=valnum.dtype)

    for row in range(ref_shape[0]):
        for col in range(ref_shape[1]):
            resnum[row, col] = np.bincount(
                valnum[row*dcell:row*dcell+dcell, col*dcell : col*dcell+dcell].reshape(dcell*dcell)
            ).argmax()
    
    # Export out raster
    return obj_to_rst(resnum, out_rst, refsrc, noData=get_nd(valsrc))

