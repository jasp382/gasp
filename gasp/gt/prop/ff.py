"""
File Format Properties
"""

def vector_formats():
    return [
        '.shp', '.gml', '.json', '.geojson', '.kml'
    ]


def raster_formats():
    return [
        '.tiff', '.tif', '.img', '.nc', 'ecw', '.jpg', '.png', '.vrt', '.jp2',
        '.asc'
    ]


def check_isRaster(_file):
    from gasp.pyt.oss import get_fileformat

    rst_lst = raster_formats()
    
    file_ext = get_fileformat(_file)
    
    if file_ext not in rst_lst:
        return None
    else:
        return True


def check_isShp(_file):
    from gasp.pyt.oss import get_fileformat
    
    lst = vector_formats()
    
    file_ext = get_fileformat(_file)
    
    if file_ext not in lst:
        return None
    else:
        return True


"""
GDAL Drivers Name
"""

def drv_name(_file):
    """
    Return the driver for a given file format
    """
    
    import os
    
    drv = {
        # Vector files
        '.gml'    : 'GML',
        '.shp'    : 'ESRI Shapefile',
        '.json'   : 'GeoJSON',
        '.kml'    : 'KML',
        '.osm'    : 'OSM',
        '.dbf'    : 'ESRI Shapefile',
        '.vct'    : 'Idrisi',
        '.nc'     : 'netCDF',
        '.vrt'    : 'VRT',
        '.mem'    : 'MEMORY',
        '.sqlite' : 'SQLite',
        '.gdb'    : 'FileGDB',
        # Raster files
        '.tif'    : 'GTiff',
        '.ecw'    : 'ECW',
        '.mpr'    : 'ILWIS',
        '.mpl'    : 'ILWIS',
        '.jpg'    : 'JPEG',
        '.nc'     : 'netCDF',
        '.png'    : 'PNG',
        '.vrt'    : 'VRT',
        '.asc'    : 'AAIGrid'
    }
    return str(drv[os.path.splitext(_file)[1]])


"""
GRASS GIS Drivers
"""

def VectorialDrivers():
    return {
        '.shp' : 'ESRI_Shapefile',
        '.gml' : 'GML'
    }


def grs_rst_drv():
    return {
        '.tif': 'GTiff',
        '.img': 'HFA'
    }
