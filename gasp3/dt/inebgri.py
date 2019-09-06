"""
Do things with BGRI from INE
"""

"""
Using GeoPandas
"""
def join_bgrishp_with_bgridata(bgriShp, bgriCsv, outShp,
                               shpJoinField="BGRI11",
                               dataJoinField="GEO_COD",
                               joinFieldsMantain=None,
                               newNames=None):
    """
    Join BGRI ESRI Shapefile with the CSV with the BGRI Data
    """
    
    from gasp3           import goToList
    from gasp3.dt.fm     import tbl_to_obj
    from gasp3.dt.to.shp import df_to_shp
    
    # Read main_table
    mainDf = tbl_to_obj(bgriShp)
    
    # Read join table
    joinDf = tbl_to_obj(bgriCsv, _delimiter=';', encoding_='utf-8')
    
    # Sanitize GEO_COD of bgriCsv
    joinDf[dataJoinField] = joinDf[dataJoinField].str.replace("'", "")
    
    if joinFieldsMantain:
        joinFieldsMantain = goToList(joinFieldsMantain)
        
        dropCols = []
        for col in joinDf.columns.values:
            if col not in [dataJoinField] + joinFieldsMantain:
                dropCols.append(col)
        
        joinDf.drop(dropCols, axis=1, inplace=True)
    
    resultDf = mainDf.merge(
        joinDf, how='inner', left_on=shpJoinField, right_on=dataJoinField
    )
    if newNames:
        newNames = goToList(newNames)
        renDict = {
            joinFieldsMantain[n] : newNames[n] for n in range(len(joinFieldsMantain))
        }
        
        resultDf.rename(columns=renDict, inplace=True)
    
    df_to_shp(resultDf, outShp)
    
    return outShp

