"""
Extraction Operations using OSM Data
"""

def osmosis_extract(boundary, osmdata, wepsg, output):
    """
    Extract OSM Data from a xml file with osmosis
    
    The extraction is done using the extent of a boundary
    """
    
    import os; from osgeo import ogr
    from gasp3            import exec_cmd
    from gasp3.gt.prop.ff import drv_name
    from gasp3.gt.mng.prj import project_geom
    
    # Assuming that boundary has only one feature
    # Get Geometry
    dtSrc = ogr.GetDriverByName(drv_name(boundary)).Open(boundary)
    lyr   = dtSrc.GetLayer()
    
    if os.path.isdir(output):
        from gasp3.pyt.oss import get_filename
        
        geoms    = []
        outFiles = []
        
        name_out = get_filename(osmdata)
        for feat in lyr:
            geoms.append(feat.GetGeometryRef())
            
            outFiles.append(os.path.join(output, "{}_{}.xml".format(
                name_out, str(feat.GetFID())
            )))
        
    else:
        for feat in lyr:
            geoms = [feat.GetGeometryRef()]
            break
        
        outFiles = [output]
    
    for g in range(len(geoms)):
        # Convert boundary to WGS84 -EPSG 4326
        geom_wgs = project_geom(
            geoms[g], int(wepsg), 4326, api='ogr'
        ) if int(wepsg) != 4326 else geoms[g]
    
        # Get boundary extent
        left, right, bottom, top = geom_wgs.GetEnvelope()
    
        # Osmosis shell comand
        osmExt = os.path.splitext(osmdata)[1]
        osm_f  = 'enableDateParsing=no' \
            if osmExt == '.xml' or osmExt == '.osm' else ''
    
        cmd = (
            'osmosis --read-{_f} {p} file={_in} --bounding-box top={t} left={l}'
            ' bottom={b} right={r} --write-{outext} file={_out}'
        ).format(
            _f = 'xml' if osmExt == '.xml' or osmExt == '.osm' else 'pbf',
            p = osm_f, _in = osmdata,
            t = str(top), l = str(left), b = str(bottom), r = str(right),
            _out = outFiles[g], outext=os.path.splitext(outFiles[g])[1][1:]
        )
    
        # Execute command
        outcmd = exec_cmd(cmd)
    
    return output


def select_highways(inOsm, outOsm):
    """
    Extract some tag from OSM file
    """
    
    import os
    from gasp3 import exec_cmd
    
    outExt = os.path.splitext(outOsm)[1]
    
    cmd = (
        'osmosis --read-xml enableDateParsing=no file={} --tf accept-ways '
        'highway=* --used-node --write-{} {}' 
    ).format(
        inOsm,
        "pbf" if outExt == ".pbf" else "xml", outOsm)
    
    outcmd = exec_cmd(cmd)
    
    return outOsm
