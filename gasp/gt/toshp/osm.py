"""
From OpenStreetMap to Feature Class
"""

def osm_to_featcls(xmlOsm, output, fileFormat='.shp', useXmlName=None,
                   outepsg=4326):
    """
    OSM to ESRI Shapefile
    """

    import os
    from gasp.gt.attr      import sel_by_attr
    from gasp.pyt.oss      import fprop, del_file
    from gasp.gt.toshp.cff import shp_to_shp
    
    # Convert xml to sqliteDB
    sqDB = shp_to_shp(xmlOsm, os.path.join(output, 'fresh_osm.sqlite'))

    # sqliteDB to Feature Class
    TABLES = {'points' : 'pnt', 'lines' : 'lnh',
              'multilinestrings' : 'mlnh', 'multipolygons' : 'poly'}
    
    for T in TABLES:
        sel_by_attr(
            sqDB, "SELECT * FROM {}".format(T),
            os.path.join(output, "{}{}{}".format(
                "" if not useXmlName else fprop(xmlOsm, 'fn') + "_",
                TABLES[T],
                fileFormat if fileFormat[0] == '.' else "." + fileFormat
            )), api_gis='ogr', oEPSG=None if outepsg == 4326 else outepsg,
            iEPSG=4326
        )
    
    # Del temp DB
    del_file(sqDB)

    return output


def getosm_to_featcls(inBoundary, outVector, boundaryEpsg=4326,
                         vectorFormat='.shp'):
    """
    Get OSM Data from the Internet and convert the file to regular vector file
    """

    import os; from gasp.gt.toosm import download_by_boundary

    # Download data from the web
    osmData = download_by_boundary(
        inBoundary, os.path.dirname(outVector), 'fresh_osm',
        boundaryEpsg, GetUrl=None
    )

    # Convert data to regular vector file
    return osm_to_featcls(
        osmData, outVector, fileFormat=vectorFormat
    )


"""
Merge OSM
"""

def osm_merge(osm_files, out_osm):
    """
    Multi OSM Files to only one file
    """

    from gasp import exec_cmd

    if type(osm_files) != list:
        raise ValueError((
            'osm_files must be a list with path to several '
            'OSM Files'
        ))
    
    if len(osm_files) == 0:
        raise ValueError((
            'osm_files must be a non empty list'
        ))

    rcmd = exec_cmd("osmium merge {} -o {}".format(
        " ".join(osm_files), out_osm
    ))

    return out_osm
