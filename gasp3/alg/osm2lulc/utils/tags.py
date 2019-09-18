"""
Tools see which OSM tags are not being used in OSM2LULC
"""

def get_not_used_tags(OSM_FILE, OUT_TBL):
    """
    Use a file OSM to detect tags not considered in the
    OSM2LULC procedure
    """
    
    import os; from gasp3.to      import obj_to_tbl
    from gasp3.gt.anls.exct       import sel_by_attr
    from gasp3.sql.fm             import Q_to_df
    from gasp3.pyt.oss            import get_filename
    from gasp3.alg.osm2lulc.utils import osm_to_sqdb
    
    OSM_TAG_MAP = {
        "DB"        : os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'osmtolulc.sqlite'
        ),
        "OSM_FEAT"  : "osm_features",
        "KEY_COL"   : "key",
        "VALUE_COL" : "value",
        "GEOM_COL"  : "geom"
    }
    
    WORKSPACE = os.path.dirname(OUT_TBL)
    
    sqdb = osm_to_sqdb(
        OSM_FILE, os.path.join(WORKSPACE, get_filename(OSM_FILE) + '.sqlite')
    )
    
    # Get Features we are considering
    ourOSMFeatures = Q_to_df(OSM_TAG_MAP["DB"], (
        "SELECT {key} AS key_y, {value} AS value_y, {geom} AS geom_y "
        "FROM {tbl}"
    ).format(
        key=OSM_TAG_MAP["KEY_COL"], value=OSM_TAG_MAP["VALUE_COL"],
        geom=OSM_TAG_MAP["GEOM_COL"], tbl=OSM_TAG_MAP["OSM_FEAT"]
    ), db_api='sqlite')
    
    # Get Features in File
    TABLES_TAGS = {
        'points'        : ['highway', 'man_made', 'building'],
        'lines'         : ['highway', 'waterway', 'aerialway', 'barrier',
                           'man_made', 'railway'],
        'multipolygons' : ['aeroway', 'amenity', 'barrier', 'building',
                           'craft', 'historic', 'land_area', ''
                           'landuse', 'leisure', 'man_made', 'military',
                           'natural', 'office', 'place', 'shop',
                           'sport', 'tourism', 'waterway', 'power',
                           'railway', 'healthcare', 'highway']
    }
    
    Qs = [
        " UNION ALL ".join([(
            "SELECT '{keycol}' AS key, {keycol} AS value, "
            "'{geomtype}' AS geom FROM {tbl} WHERE "
            "{keycol} IS NOT NULL"
        ).format(
            keycol=c, geomtype='Point' if table == 'points' else 'Line' \
                if table == 'lines' else 'Polygon',
            tbl=table
        ) for c in TABLES_TAGS[table]]) for table in TABLES_TAGS
    ]
    
    fileOSMFeatures = Q_to_df(sqdb, (
        "SELECT key, value, geom FROM ({}) AS foo "
        "GROUP BY key, value, geom"
    ).format(" UNION ALL ".join(Qs)), db_api='sqlite')
    
    _fileOSMFeatures = fileOSMFeatures.merge(
        ourOSMFeatures, how='outer',
        left_on=["key", "value", "geom"],
        right_on=["key_y", "value_y", "geom_y"]
    )
    
    # Select OSM Features of file without correspondence
    _fileOSMFeatures["isnew"] =_fileOSMFeatures.key_y.fillna(value='nenhum')
    
    newTags = _fileOSMFeatures[_fileOSMFeatures.isnew == 'nenhum']
    
    newTags["value"] = newTags.value.str.replace("'", "''")
    
    newTags["whr"] = newTags.key.str.encode('utf-8').astype(str) + "='" + \
        newTags.value.str.encode('utf-8').astype(str) + "'"
    
    # Export OUT_TBL with tags not being used
    obj_to_tbl(newTags, OUT_TBL, sheetsName="new_tags", sanitizeUtf8=True)
    
    # Export tags not being used to new shapefile
    def to_regular_str(row):
        san_str = row.whr
        
        row["whr_san"] = san_str
        
        return row
    
    for t in TABLES_TAGS:
        if t == 'points':
            filterDf = newTags[newTags.geom == 'Point']
        
        elif t == 'lines':
            filterDf = newTags[newTags.geom == 'Line']
        
        elif t == 'multipolygons':
            filterDf = newTags[newTags.geom == 'Polygon']
        
        Q = "SELECT * FROM {} WHERE {}".format(
            t, filterDf.whr.str.cat(sep=" OR "))
        
        try:
            shp = sel_by_attr(
                sqdb, Q, os.path.join(WORKPSACE, t + '.shp'), api_gis='ogr'
            )
        except:
            __filterDf = filterDf.apply(lambda x: to_regular_str(x), axis=1)
            
            _Q = "SELECT * FROM {} WHERE {}".format(
                t, __filterDf.whr_san.str.cat(sep=" OR ")
            )
            
            shp = sel_by_attr(sqdb, _Q, os.path.join(WORKSPACE, t + '.shp'))
    
    return OUT_TBL

