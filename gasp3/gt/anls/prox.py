"""
Buffering Tools
"""

def ogr_buffer(geom, radius, out_file, srs=None):
    """
    For each geometry in the input, this method create a buffer and store it
    in a vetorial file
    
    Accepts files or lists with geom objects as inputs
    """
    
    from osgeo             import ogr
    from gasp3.gt.mng.prj  import ogr_def_proj
    from gasp3.gt.prop.ff  import drv_name
    from gasp3.gt.prop.prj import get_sref_from_epsg
    
    # Create output
    buffer_shp = ogr.GetDriverByName(
        drv_name(out_file)).CreateDataSource(out_file)
    
    buffer_lyr = buffer_shp.CreateLayer(
        os.path.splitext(os.path.basename(out_file))[0],
        get_sref_from_epsg(srs) if srs else None,
        geom_type=ogr.wkbPolygon
    )
    
    featDefn = buffer_lyr.GetLayerDefn()
    
    if type(geom) == list:
        for g in geom:
            feat = ogr.Feature(featDefn)
            feat.SetGeometry(draw_buffer(g, radius))
            
            buffer_lyr.CreateFeature(feat)
            
            feat = None
        
        buffer_shp.Destroy()
    
    elif type(geom) == dict:
        if 'x' in geom and 'y' in geom:
            X='x'; Y='y'
        elif 'X' in geom and 'Y' in geom:
            X='X'; Y='Y'
        else:
            raise ValueError((
                'Your geom dict has invalid keys. '
                'Please use one of the following combinations: '
                'x, y; '
                'X, Y'
            ))
        
        from gasp3.dt.to.geom import create_point
        feat = ogr.Feature(featDefn)
        g = create_point(geom[X], geom[Y], api='ogr')
        feat.SetGeometry(draw_buffer(g, radius))
        
        buffer_lyr.CreateFeature(feat)
        
        feat = None
        
        buffer_shp.Destroy()
        
        if srs:
            ogr_def_proj(out_file, epsg=srs)
    
    elif type(geom) == str or type(geom) == unicode:
        # Check if the input is a file
        if os.path.exists(geom):
            inShp = ogr.GetDriverByName(drv_name(geom)).Open(geom, 0)
            
            lyr = inShp.GetLayer()
            for f in lyr:
                g = f.GetGeometryRef()
                
                feat = ogr.Feature(featDefn)
                feat.SetGeometry(draw_buffer(g, radius))
                
                buffer_lyr.CreateFeature(feat)
                
                feat = None
            
            buffer_shp.Destroy()
            inShp.Destroy()
            
            if srs:
                ogr_def_proj(out_file, epsg=srs)
            else:
                ogr_def_proj(out_file, template=geom)
            
        else:
            raise ValueError('The given path does not exist')
    
    else:
        raise ValueError('Your geom input is not valid')
    
    return out_file

