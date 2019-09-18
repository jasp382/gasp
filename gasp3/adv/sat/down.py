"""
Download Sentinel Data
"""

URL_COPERNICUS = 'https://scihub.copernicus.eu/dhus'

def lst_prod(shpExtent, start_time, end_time, user, password,
             outShp, platname, procLevel):
    """
    List Sentinel Products for one specific area
    
    platformname:
    * Sentinel-1
    * Sentinel-2
    * Sentinel-3

    processinglevel:
    * Level-1A
    * Level-1B
    * Level-1C
    * Level-2A
    ...
    """
    # TODO: Filter by cloud cover
    
    import os
    from sentinelsat     import SentinelAPI, read_geojson, geojson_to_wkt
    from datetime        import date
    from gasp3.fm        import tbl_to_obj
    from gasp3.pyt.oss   import get_fileformat
    from gasp3.gt.to.shp import df_to_shp
    
    # Get Search Area
    
    if get_fileformat(shpExtent) == '.json':
        boundary = geojson_to_wkt(shpExtent)
    
    else:
        boundary = tbl_to_obj(
            shpExtent, output='array', fields="ALL",
            geomAsWkt=True, srsTo=4326
        )[0]["GEOM"]
    
    # Create API instance
    api = SentinelAPI(user, password, URL_COPERNICUS)
    
    # Search for products
    products = api.query(
        boundary, date=(start_time, end_time),
        platformname=platname,
        cloudcoverpercentage=(0, 30),
        processinglevel=procLevel
    )
    
    df_prod = api.to_geodataframe(products)
    
    df_prod['ingestiondate'] = df_prod.ingestiondate.astype(str)
    df_prod['beginposition'] = df_prod.beginposition.astype(str)
    df_prod['endposition']   = df_prod.endposition.astype(str)
    
    # Export results to Shapefile
    return df_to_shp(df_prod, outShp)


def down_imgs(inTbl, user, password, imgIDcol, outFolder=None):
    """
    Download Images in Table
    """
    
    import os
    from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
    from gasp3.fm    import tbl_to_obj
    
    of = outFolder if outFolder else os.path.dirname(inTbl)
    
    # Tbl to df
    df_img = tbl_to_obj(inTbl)
    
    # API Instance
    api = SentinelAPI(user, password, URL_COPERNICUS)
    
    # Download Images
    for idx, row in df_img.iterrows():
        # Check if file already exists
        outFile = os.path.join(outFolder, row.identifier + '.zip')
        
        if os.path.exists(outFile):
            print('IMG already exists')
            continue
        else:
            api.download(row[imgIDcol], directory_path=outFolder)

