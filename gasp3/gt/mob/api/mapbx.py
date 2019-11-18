"""
MapBox API Tools
"""

def matrix_od(originsShp, destinationShp, originsEpsg, destinationEpsg,
              resultShp, modeTrans="driving"):
    """
    Use Pandas to Retrieve data from MapBox Matrix OD Service
    """
    
    import time; from threading import Thread
    from gasp3.adv.mob.mapbx import get_keys,matrix
    from gasp3.fm            import tbl_to_obj
    from gasp3.pyt.df.split  import split_df, split_df_inN
    from gasp3.pyt.df.fld    import listval_to_newcols
    from gasp3.pyt.df.fld    import pointxy_to_cols
    from gasp3.gt.prj        import proj
    from gasp3.pyt.df.mng    import merge_df
    from gasp3.gt.prop.feat  import get_gtype
    from gasp3.gt.to.shp     import df_to_shp
    
    # Data to GeoDataFrame
    origens  = tbl_to_obj(    originsShp)
    destinos = tbl_to_obj(destinationShp)
    
    # Check if SHPs are points
    inGeomType = get_gtype(origens, geomCol="geometry", gisApi='pandas')
    
    if inGeomType != 'Point' and inGeomType != 'MultiPoint':
        raise ValueError('The input geometry must be of type point')
    
    inGeomType = get_gtype(destinos, geomCol="geometry", gisApi='pandas')
    
    if inGeomType != 'Point' and inGeomType != 'MultiPoint':
        raise ValueError('The input geometry must be of type point')
    
    # Re-Project data to WGS
    if originsEpsg != 4326:
        origens = proj(origens, None, 4326, gisApi='pandas')
    
    if destinationEpsg != 4326:
        destinos = proj(destinos, None, 4326, gisApi='pandas')
    
    origens = pointxy_to_cols(
        origens, geomCol="geometry",
        colX="longitude", colY="latitude"
    ); destinos = pointxy_to_cols(
        destinos, geomCol="geometry",
        colX="longitude", colY="latitude"
    )
    
    # Prepare coordinates Str
    origens["location"]  = origens.longitude.astype(str) \
        + "," + origens.latitude.astype(str)
    
    destinos["location"] = destinos.longitude.astype(str) \
        + "," + destinos.latitude.astype(str)
    
    # Split destinations DataFrame into Dafaframes with
    # 24 rows
    lst_destinos = split_df(destinos, 24)
    
    # Get Keys to use
    KEYS = get_keys()
    # Split origins by key
    origensByKey = split_df_inN(origens, KEYS.shape[0])
    
    lst_keys= KEYS["key"].tolist()
    
    # Produce matrix
    results = []
    def get_matrix(origins, key):
        def def_apply(row):
            rowResults = []
            for df in lst_destinos:
                strDest = df.location.str.cat(sep=";")
                
                strLocations = row["location"] + ";" + strDest
                
                dados = matrix(
                    strLocations, idxSources="0",
                    idxDestinations=";".join([str(i) for i in range(1, df.shape[0] + 1)]),
                    useKey=key, modeTransportation=modeTrans
                )
                time.sleep(5)
                
                rowResults += dados["durations"][0]
            
            row["od_matrix"] = rowResults
            
            return row
        
        newOrigins = origins.apply(
            lambda x: def_apply(x), axis=1
        )
        
        results.append(newOrigins)
    
    # Create threads
    thrds = []
    i     = 1
    for df in origensByKey:
        thrds.append(Thread(
            name="tk{}".format(str(i)), target=get_matrix,
            args=(df, lst_keys[i - 1])
        ))
        i += 1
    
    # Start all threads
    for thr in thrds:
        thr.start()
    
    # Wait for all threads to finish
    for thr in thrds:
        thr.join()
    
    # Join all dataframes
    RESULT = merge_df(results, ignIndex=False)
    
    RESULT = listval_to_newcols(RESULT, "od_matrix")
    
    RESULT.rename(
        columns={
            c: "dest_{}".format(c)
            for c in RESULT.columns.values if type(c) == int or type(c) == long
        }, inplace=True
    )
    
    if originsEpsg != 4326:
        RESULT = proj(RESULT, None, originsEpsg, gisApi='pandas')
    
    return df_to_shp(RESULT, resultShp)


    
    return results