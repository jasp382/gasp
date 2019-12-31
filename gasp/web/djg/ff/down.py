"""
Pseudo Views for download
"""


def down_zip(fileDir, fileName, fileFormat):
    """
    Prepare Download response for a zipped file
    """
    
    import os
    from django.http import HttpResponse
    
    zipFile = os.path.join(
        fileDir,
        '{}.{}'.format(fileName, fileFormat)
    )
    with open(zipFile, 'rb') as f:
        r = HttpResponse(f.read())
        
        r['content_type'] = 'application/zip'
        r['Content-Disposition'] = 'attachment;filename={}.{}'.format(
            fileName, fileFormat
        )
        
        return r


def down_xml(fileXml):
    """
    Prepare Download response for a xml file
    """
    
    import os
    from django.http import HttpResponse
    
    with open(fileXml, 'rb') as f:
        r = HttpResponse(f.read())
        
        r['content_type'] = 'text/xml'
        
        r['Content-Disposition'] = 'attachment;filename={}'.format(
            os.path.basename(fileXml)
        )
        
        return r


def down_tiff(tifFile):
    """
    Download tif image
    """
    
    import os; from django.http import HttpResponse
    
    with open(tifFile, mode='rb') as img:
        r = HttpResponse(img.read())
        
        r['content_type'] = 'image/tiff'
        r['Content-Disposition'] = 'attachment;filename={}'.format(
            os.path.basename(tifFile)
        )
        return r


def mdl_to_kml(mdl, outKml, filter=None):
    """
    Query a database table and convert it to a KML File
    """
    
    import json;                 import os
    from django.http             import HttpResponse
    from gasp.pyt.oss            import get_filename
    from gasp.web.djg.mdl.serial import mdl_serialize_to_json
    from gasp.gt.to.shp          import shp_to_shp
    
    # Write data in JSON
    JSON_FILE = os.path.join(
        os.path.dirname(outKml), get_filename(outKml) + '.json'
    )
    
    mdl_serialize_to_json(mdl, 'geojson', JSON_FILE, filterQ=filter)
    
    # Convert JSON into KML
    shp_to_shp(JSON_FILE, outKml, gisApi='ogr')
    
    # Create a valid DOWNLOAD RESPONSE
    with open(outKml, 'rb') as f:
        response = HttpResponse(f.read())
        
        response['content_type'] = 'text/xml'
        response['Content-Disposition'] = 'attachment;filename={}'.format(
            os.path.basename(outKml)
        )
        
        return response
