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
    
    from gasp3.pyt.oss import get_fileformat
    
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
        from gasp3 import goToList
        
        sheet = 0 if sheet == None else sheet
        
        indexCol = 0 if useFirstColAsIndex else None
        
        tableDf = pandas.read_excel(
            tblFile, sheet, index_col=indexCol,
            encoding='utf-8', dtype='object',
            usecols=goToList(fields) if fields != "ALL" else None
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
                from gasp3.gt.mng.fld.df import del_fld_notin_geodf
                
                tableDf = del_fld_notin_geodf(tableDf, fields, geomCol=geomCol)
            
            if srsTo:
                from gasp3.gt.mng.prj import project
                
                tableDf = project(tableDf, None, srsTo, gisApi='pandas')
            
            tableDf.rename(columns={geomCol : "GEOM"}, inplace=True)
            
            if geomAsWkt:
                tableDf["GEOM"] = tableDf.GEOM.astype(str)
    
    else:
        raise ValueError('{} is not a valid table format!'.format(fFormat))
    
    if fFormat != '.shp' and fields != "ALL":
        from gasp3 import goToList
        
        fields = goToList(fields)
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

