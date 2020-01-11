"""
Tables to Pandas Dataframe
"""

def tbl_to_obj(tblFile, sheet=None, useFirstColAsIndex=None,
              _delimiter=None, encoding_='utf8', output='df',
              fields="ALL", geomCol=None, colsAsArray=None,
              geomAsWkt=None, srsTo=None):
    """
    Table File to Pandas DataFrame
    
    output Options:
    - df;
    - dict;
    - array;
    """
    
    from gasp.pyt.oss import get_fileformat
    
    fFormat = get_fileformat(tblFile)
    
    if fFormat == '.dbf':
        """
        Convert dBase to Pandas Dataframe
        """
        
        from simpledbf import Dbf5
        
        dbfObj = Dbf5(tblFile)
        
        tableDf = dbfObj.to_dataframe()
    
    elif fFormat == '.ods':
        """
        ODS file to Pandas Dataframe
        """
        
        import json
        import pandas
        from pyexcel_ods import get_data
        
        if not sheet:
            raise ValueError("You must specify sheet name when converting ods files")
        data = get_data(tblFile)[sheet]
        
        tableDf = pandas.DataFrame(data[1:], columns=data[0])
    
    elif fFormat == '.xls' or fFormat == '.xlsx':
        """
        XLS to Pandas Dataframe
        """
        
        import pandas
        from gasp.pyt import obj_to_lst
        
        sheet = 0 if not sheet else sheet
        
        indexCol = 0 if useFirstColAsIndex else None
        
        tableDf = pandas.read_excel(
            tblFile, sheet, index_col=indexCol,
            encoding='utf-8', dtype='object',
            usecols=obj_to_lst(fields) if fields != "ALL" else None
        )
    
    elif fFormat == '.txt' or fFormat == '.csv':
        """
        Text file to Pandas Dataframe
        """
        
        import pandas
        
        if not _delimiter:
            raise ValueError(
                "You must specify _delimiter when converting txt files"
            )
        
        tableDf = pandas.read_csv(
            tblFile, sep=_delimiter, low_memory=False,
            encoding=encoding_
        )
    
    elif fFormat == '.shp':
        """
        ESRI Shapefile to Pandas Dataframe
        """
        
        import geopandas
        
        tableDf = geopandas.read_file(tblFile)
        
        if output != 'df':
            if not geomCol:
                for c in tableDf.columns.values:
                    if c == 'geometry' or c == 'geom':
                        geomCol = c
                        break
            
            if fields != "ALL":
                from gasp.df.fld import del_fld_notin_geodf
                
                tableDf = del_fld_notin_geodf(tableDf, fields, geomCol=geomCol)
            
        if srsTo:
            from gasp.gt.prj import proj
                
            tableDf = proj(tableDf, None, srsTo, gisApi='pandas')
            
        tableDf.rename(columns={geomCol : "GEOM"}, inplace=True)
            
        if geomAsWkt:
            tableDf["GEOM"] = tableDf.GEOM.astype(str)
    
    else:
        raise ValueError('{} is not a valid table format!'.format(fFormat))
    
    if fFormat != '.shp' and fields != "ALL":
        from gasp.pyt import obj_to_lst
        
        fields = obj_to_lst(fields)
        if fields:
            delCols = []
            for fld in list(tableDf.columns.values):
                if fld not in fields:
                    delCols.append(fld)
            
            if delCols:
                tableDf.drop(delCols, axis=1, inplace=True)
    
    if output != 'df':
        if output == 'dict':
            orientation = "index" if not colsAsArray else "list"
        
        elif output == 'array':
            tableDf["FID"] = tableDf.index
            
            orientation = "records"
        
        tableDf = tableDf.to_dict(orient=orientation)
    
    return tableDf



"""
Tables to Pandas DataFrame
"""

def points_to_list(pntShp, listVal='tuple', inEpsg=None, outEpsg=None):
    """
    Return a list as:
    
    if listVal == 'tuple'
    l = [(x_coord, y_coord), ..., (x_coord, y_coord)]
    
    elif listVal == 'dict'
    l = [
        {id : fid_value, x : x_coord, y : y_coord},
        ...
        {id : fid_value, x : x_coord, y : y_coord}
    ]
    """
    
    geoDf = tbl_to_obj(pntShp)
    
    if inEpsg and outEpsg:
        if inEpsg != outEpsg:
            from gasp.gt.prj import proj
            
            geoDf = proj(geoDf, None, outEpsg, gisApi='pandas')
    
    geoDf["x"] = geoDf.geometry.x.astype(float)
    geoDf["y"] = geoDf.geometry.y.astype(float)
    
    if listVal == 'tuple':
        subset = geoDf[['x', 'y']]
    
        coords = [tuple(x) for x in subset.values]
    
    elif listVal == 'dict':
        geoDf["id"] = geoDf.index
        subset = geoDf[['id', 'x', 'y']]
        
        coords = subset.to_dict(orient='records')
    
    else:
        raise ValueError(
            'Value of listVal is not Valid. Please use "tuple" or "dict"'
        )
    
    return coords
