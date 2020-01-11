"""
Terrain
"""


###############################################################################
###############################################################################
"""
Run this beutiful script
"""

if __name__ == '__main__':
    """
    Parameters
    """

    lmt_fld       = '/home/gisuser/mdt/lmt_rst'
    countours_fld = '/home/gisuser/mdt/countours'
    dem_fld       = '/home/gisuser/mdt/dems'
    elv_fld       = 'data'
    masks         = '/home/gisuser/mdt/rst_masks'

    """
    Run Script
    """

    from gasp.gd.terrain.grs import thrd_dem

    thrd_dem(
        countours_fld, lmt_fld, dem_fld, elv_fld,
        refFormat='.tif', countoursFormat='.shp', demFormat='.tif',
        cellsize=10, masksFolder=masks, masksFormat='.tif'
    )

