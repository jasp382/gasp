"""
Multi-Files to Single File
"""

def shps_to_shp(shps, outShp, api="ogr2ogr", fformat='.shp',
    dbname=None):
    """
    Get all features in several Shapefiles and save them in one file

    api options:
    * ogr2ogr;
    * psql;
    * pandas;
    * psql;
    """

    import os

    if type(shps) != list:
        # Check if is dir
        if os.path.isdir(shps):
            from gasp.pyt.oss import lst_ff
            # List shps in dir
            shps = lst_ff(shps, file_format=fformat)
        
        else:
            raise ValueError((
                'shps should be a list with paths for Feature Classes or a path to '
                'folder with Feature Classes'
            ))

    
    if api == "ogr2ogr":
        from gasp            import exec_cmd
        from gasp.gt.prop.ff import drv_name
        
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
        
        from gasp.gt.fmshp import shp_to_obj
        from gasp.gt.toshp import df_to_shp
        
        if type(shps) != list:
            raise ValueError('shps should be a list with paths for Feature Classes')
        
        dfs = [shp_to_obj(shp) for shp in shps]
        
        result = dfs[0]
        
        for df in dfs[1:]:
            result = result.append(df, ignore_index=True, sort=True)
        
        df_to_shp(result, outShp)
    
    elif api == 'psql':
        import os
        from gasp.sql.tbl import tbls_to_tbl, del_tables
        from gasp.gql.to  import shp_to_psql

        if not dbname:
            from gasp.sql.db import create_db

            create_db(dbname, api='psql')

        pg_tbls = shp_to_psql(
            dbname, shps, api="shp2pgsql"
        )

        if os.path.isfile(outShp):
            from gasp.pyt.oss import fprop
            outbl = fprop(outShp, 'fn')
        
        else:
            outbl = outShp

        tbls_to_tbl(dbname, pg_tbls, outbl)

        if outbl != outShp:
            from gasp.gt.toshp.db import dbtbl_to_shp

            dbtbl_to_shp(
                dbname, outbl, 'geom', outShp, inDB='psql',
                api="pgsql2shp"
            )

        del_tables(dbname, pg_tbls)
    
    elif api == 'grass':
        from gasp import exec_cmd

        rcmd = exec_cmd((
            "v.patch input={} output={} --overwrite --quiet"
        ).format(",".join(shps), outShp))
       
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
    
    import os
    from gasp.pyt       import obj_to_lst
    from gasp.gt.fmshp  import shp_to_obj
    from gasp.pyt.df.to import merge_df
    from gasp.gt.toshp  import df_to_shp
    
    EXT = os.path.splitext(inShps[0])[1]
    
    shpDfs = [shp_to_obj(shp) for shp in inShps]
    
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

