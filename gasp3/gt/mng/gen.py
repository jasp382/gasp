"""
General tools
"""


def copy_feat(inShp, outShp, gisApi='arcpy', outDefn=None, only_geom=None):
    """
    Copy Features to a new Feature Class
    """
    
    if gisApi == 'arcpy':
        import arcpy
        
        arcpy.CopyFeatures_management(inShp, outShp, "", "", "", "")
    
    elif gisApi == 'ogrlyr':
        """
        Copy the features of one layer to another layer...
    
        If the layers have the same fields, this method could also copy
        the tabular data
    
        TODO: See if the input is a layer or not and make arrangements
        """
        
        from osgeo import ogr
        
        for f in inShp:
            geom = f.GetGeometryRef()
        
            new = ogr.Feature(outDefn)
        
            new.SetGeometry(geom)
        
        # Copy tabular data
        if not only_geom:
            for i in range(0, outDefn.GetFieldCount()):
                new.SetField(outDefn.GetFieldDefn(i).GetNameRef(), f.GetField(i))
        
        outShp.CreateFeature(new)
        
        new.Destroy()
        f.Destroy()
        
        return None
    
    else:
        raise ValueError('Sorry, API {} is not available'.format(gisApi))
    
    return outShp


def merge_feat(shps, outShp, api="ogr2ogr"):
    """
    Get all features in several Shapefiles and save them in one file
    """
    
    if api == "ogr2ogr":
        from gasp3            import exec_cmd
        from gasp3.gt.prop.ff import drv_name
        
        out_drv = drv_name(outShp)
        
        # Create output and copy some features of one layer (first in shps)
        cmdout = exec_cmd('ogr2ogr -f "{}" {} {}'.format(
            out_drv, outShp, shps[0]
        ))
        
        # Append remaining layers
        lcmd = [exec_cmd(
            'ogr2ogr -f "{}" -update -append {} {}'.format(
                out_drv, outShp, shps[i]
            )
        ) for i in range(1, len(shps))]
    
    elif api == 'pandas':
        """
        Merge SHP using pandas
        """
        
        from gasp3.fm        import tbl_to_obj
        from gasp3.gt.to.shp import df_to_shp
        
        if type(shps) != list:
            raise ValueError('shps should be a list with paths for Feature Classes')
        
        dfs = [tbl_to_obj(shp) for shp in shps]
        
        result = dfs[0]
        
        for df in dfs[1:]:
            result = result.append(df, ignore_index=True, sort=True)
        
        df_to_shp(result, outShp)
    
    else:
        raise ValueError(
            "{} API is not available"
        )
    
    return outShp


def same_attr_to_shp(inShps, interestCol, outFolder, basename="data_",
                     resultDict=None):
    """
    For several SHPS with the same field, this program will list
    all values in such field and will create a new shp for all
    values with the respective geometry regardeless the origin shp.
    """
    
    import os; from gasp3 import goToList
    from gasp3.fm         import tbl_to_obj
    from gasp3.df.mng     import merge_df
    from gasp3.gt.to.shp  import df_to_shp
    
    EXT = os.path.splitext(inShps[0])[1]
    
    shpDfs = [tbl_to_obj(shp) for shp in inShps]
    
    DF = merge_df(shpDfs, ignIndex=True)
    #DF.dropna(axis=0, how='any', inplace=True)
    
    uniqueVal = DF[interestCol].unique()
    
    nShps = [] if not resultDict else {}
    for val in uniqueVal:
        ndf = DF[DF[interestCol] == val]
        
        KEY = str(val).split('.')[0] if '.' in str(val) else str(val)
        
        nshp = df_to_shp(ndf, os.path.join(
            outFolder, '{}{}{}'.format(basename, KEY, EXT)
        ))
        
        if not resultDict:
            nShps.append(nshp)
        else:
            nShps[KEY] = nshp
    
    return nShps

