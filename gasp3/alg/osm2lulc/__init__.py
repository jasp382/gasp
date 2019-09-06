"""
Execute OSM2LULC Algorithm
"""

def osm_to_lulc(__VERSION, OSM_DATA, NOMENCLATURE, REF_RASTER, RESULT,
                SRS_CODE=3857, REWRITE=None, DATAFOLDER=None):
    """
    __VERSION options:
    * GRASS_VECTOR;
    * GRASS_SQLITE_VECTOR;
    * GRASS_RASTER;
    * NUMPY_RASTER.
    
    ROADS OPTIONS:
    * GRASS;
    * SQLITE.
    """
    
    if __VERSION == "GRASS_RASTER":
        from gasp3.alg.osm2lulc.grs import raster_based
        
        rr = raster_based(
            OSM_DATA, NOMENCLATURE, REF_RASTER, RESULT,
            epsg=SRS_CODE, overwrite=REWRITE, dataStore=DATAFOLDER
        )
    
    elif __VERSION == "GRASS_VECTOR":
        from gasp3.alg.osm2lulc.grs import vector_based
        
        rr = vector_based(
            OSM_DATA, NOMENCLATURE, REF_RASTER, RESULT,
            epsg=SRS_CODE, overwrite=REWRITE, dataStore=DATAFOLDER,
            RoadsAPI="GRASS"
        )
    
    elif __VERSION == "GRASS_SQLITE_VECTOR":
        from gasp3.alg.osm2lulc.grs import vector_based
        
        rr = vector_based(
            OSM_DATA, NOMENCLATURE, REF_RASTER, RESULT,
            epsg=SRS_CODE, overwrite=REWRITE, dataStore=DATAFOLDER,
            RoadsAPI="SQLITE"
        )
    
    elif __VERSION == "NUMPY_RASTER":
        from gasp3.alg.osm2lulc.num import osm2lulc
        
        rr = osm2lulc(
            OSM_DATA, NOMENCLATURE, REF_RASTER, RESULT,
            epsg=SRS_CODE, overwrite=REWRITE, dataStore=DATAFOLDER
        )
    
    else:
        raise ValueError('Version with tag {} is not available')
    
    return rr

