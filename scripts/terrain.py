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

    lmt_fld       = '/home/jasp/mdt/mdt50_lmt'
    countours_fld = '/home/jasp/mdt/countours'
    dem_fld       = '/home/jasp/mdt/dems50'
    elv_fld       = 'data'
    masks         = '/home/jasp/mdt/mdt50_masks'

    """
    Run Script
    """

    from gasp.gd.terrain.grs import thrd_dem

    thrd_dem(
        countours_fld, lmt_fld, dem_fld, elv_fld,
        refFormat='.tif', countoursFormat='.shp', demFormat='.tif',
        cellsize=10, masksFolder=masks, masksFormat='.tif'
    )

