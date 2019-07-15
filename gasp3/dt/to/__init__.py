"""
Python data to File Data
"""


def obj_to_tbl(pyObj, outTbl, delimiter=None, wIndex=None,
               sheetsName=None, sanitizeUtf8=True):
    """
    Python object to data File
    """
    
    def sanitizeP(row, cols):
        for c in cols:
            try:
                _c = int(row[c])
            except:
                try:
                    row[c] = unicode(str(row[c]), 'utf-8')
                except:
                    pass
        
        return row
    
    import pandas
    from gasp3.pyt.oss import get_fileformat
    
    ff = get_fileformat(outTbl)
    
    if ff == '.txt' or ff == '.csv' or ff == '.tsv':
        if not delimiter:
            raise ValueError((
                "To save your data into a text file, you need to give a value "
                "to the delimiter input parameter"
            ))
        
        if type(pyObj) == pandas.DataFrame:
            pyObj.to_csv(outTbl, sep=delimiter, encoding='utf-8', index=wIndex)
        
        else:
            raise ValueError((
                "pyObj has an invalid data type"
            ))
    
    elif ff == '.xlsx' or ff == '.xls':
        from gasp3         import goToList
        from gasp3.pyt.oss import get_filename
        
        dfs = [pyObj] if type(pyObj) != list else pyObj
        sheetsName = goToList(sheetsName)
        
        for df in dfs:
            if type(df) != pandas.DataFrame:
                raise ValueError("pyObj has an invalid data type")
            
        if sanitizeUtf8:
            for i in range(len(dfs)):
                COLS = list(dfs[i].columns.values)
                
                dt = dfs[i].apply(lambda x: sanitizeP(x, COLS), axis=1)
                
                dfs[i] = dt
            
        writer = pandas.ExcelWriter(outTbl, engine='xlsxwriter')
        
        for i in range(len(dfs)):
            dfs[i].to_excel(
                writer,
                sheet_name="{}_{}".format(
                    get_filename(outTbl), str(i)
                ) if not sheetsName or i+1 > len(sheetsName) else sheetsName[i],
                index=wIndex
            )
        
        writer.save()
    
    elif ff == '.dbf':
        import numpy as np
        import pandas
        import pysal
        
        type2spec = {int: ('N', 20, 0),
            np.int64: ('N', 20, 0),
            float: ('N', 36, 15),
            np.float64: ('N', 36, 15),
            str: ('C', 14, 0),
            unicode: ('C', 14, 0)
        }
        
        types = [type(pyObj[i].iloc[0]) for i in pyObj.columns]
        specs = [type2spec[t] for t in types]
        
        with pysal.open(outTbl, 'w') as db:
            db.header = list(df.columns)
            db.field_spec = specs
            for i, row in df.T.iteritems():
                db.write(row)
    
    else:
        raise ValueError('{} is not a valid table format!'.format(ff))
    
    return outTbl


def db_to_tbl(conDB, tables, outTbl, txtDelimiter=None, dbAPI='psql',
              outTblF=None, sheetsNames=None):
    """
    Database data to File table
    
    API's Avaialble:
    * psql;
    * sqlite;
    """
    
    import os
    from gasp3           import goToList
    from gasp3.dt.fm.sql import query_to_df
    
    if tables == 'ALL':
        from gasp3.sql.i import lst_tbl
        
        tables = lst_tbl(conDB, schema='public', excludeViews=True, api=dbAPI)
    else:
        tables = goToList(tables)
    
    sheetsNames = goToList(sheetsNames)
    
    outTblF = None if not outTblF else outTblF \
        if outTblF[0] == '.' else '.' + outTblF
    
    if len(tables) > 1:
        if not os.path.isdir(outTbl) or not outTblF:
            raise ValueError((
                "When tables has more than one table, "
                "outTbl must be dir and outTblF must be specified"
            ))
    
    elif len(tables) == 1:
        if os.path.isdir(outTbl) and outTblF:
            outTbl = os.path.join(outTbl, tables[0] + outTblF)
        
        elif os.path.isdir(outTbl) and not outTbl:
            raise ValueError((
                'We find only a table to export and outTbl is a dir. '
                'Please give a path to a file or specify the table format '
                'using outTblF format'
            ))
        
        else:
            outTbl = outTbl
    
    else:
        raise ValueError(
            "tables value is not valid"
        )   
    
    DFS = [query_to_df(
        conDB, t if t.startswith(
            "SELECT") else "SELECT * FROM {}".format(t), db_api=dbAPI
    ) for t in tables]
    
    if os.path.isfile(outTbl):
        from gasp3.pyt.oss import get_fileformat
        
        ff = get_fileformat(outTbl)
        
        if ff == '.xlsx' or ff == '.xls':
            obj_to_tbl(DFS, outTbl, sheetsName=sheetsNames, sanitizeUtf8=None)
            
            return outTbl
    
    for i in range(len(DFS)):
        obj_to_tbl(
            DFS[i],
            outTbl if len(DFS) == 1 else os.path.join(
                outTbl, tables[i] + outTblF
            ),
            delimiter=txtDelimiter,
            sheetsName=sheetsNames
        )
    
    return outTbl


"""
To SQL
"""

def df_to_db(conParam, df, table, append=None, api='psql'):
    """
    Pandas Dataframe to PGSQL table
    
    API options:
    * psql;
    * sqlite
    """
    
    if api != 'psql' and api != 'sqlite':
        raise ValueError('API {} is not available'.format(api))
    
    from gasp3.sql.c import alchemy_engine
    
    pgengine = alchemy_engine(conParam, api=api)
    
    df.to_sql(
        table, pgengine,
        if_exists='replace' if not append else 'append',
        index=False
    )
    
    return table


def geodf_to_psql(conParam, df, pgtable, epsg, geomType,
                  colGeom="geometry", isAppend=None):
    """
    Pandas GeoDataframe to PGSQL table
    """
    
    from geoalchemy2 import Geometry, WKTElement
    from gasp3.sql.c import alchemy_engine
    
    pgengine = alchemy_engine(conParam, api='psql')
    
    df["geom"] = df[colGeom].apply(
        lambda x: WKTElement(x.wkt, srid=epsg)
    )
    
    if colGeom != 'geom':
        df.drop(colGeom, axis=1, inplace=True)
    
    df.to_sql(
        pgtable, pgengine, if_exists='replace' if not isAppend else 'append',
        index=False, dtype={'geom' : Geometry(geomType, srid=epsg)}
    )
    
    return pgtable


def tbl_to_db(tblFile, dbCon, sqlTbl, delimiter=None, encoding_='utf-8',
              sheet=None, isAppend=None, api_db='psql'):
    """
    Table file to Database Table
    
    API's available:
    * psql;
    * sqlite;
    """
    
    import os
    from gasp3         import goToList
    from gasp3.pyt.oss import get_fileformat, get_filename
    from gasp3.dt.fm   import tbl_to_obj
    
    if os.path.isdir(tblFile):
        from gasp3.pyt.oss import list_files
        
        tbls = list_files(tblFile)
    
    else:
        tbls = goToList(tblFile)
    
    outSQLTbl = goToList(sqlTbl)
    
    RTBL = []
    for i in range(len(tbls)):
        ff = get_fileformat(tbls[i])
    
        if ff == '.csv' or ff == '.txt' or ff == '.tsv':
            if not delimiter:
                raise ValueError((
                    "To convert TXT to DB table, you need to give a value for the "
                    "delimiter input parameter"
                ))
        
            __enc = 'utf-8' if not encoding_ else encoding_
        
            data = tbl_to_obj(
                tbls[i], _delimiter=delimiter, encoding_=__enc
            )
    
        elif ff == '.dbf':
            data = tbl_to_obj(tbls[i])
    
        elif ff == '.xls' or ff == '.xlsx':
            data = tbl_to_obj(tbls[i], sheet=sheet)
    
        elif ff == '.ods':
            if not sheet:
                raise ValueError((
                    "To convert ODS to DB table, you need to give a value "
                    "for the sheet input parameter"
                ))
        
            data = tbl_to_obj(tbls[i], sheet=sheet)
    
        else:
            raise ValueError('{} is not a valid table format!'.format(fFormat))
    
        # Send data to database
        _rtbl = df_to_db(
            dbCon, data,
            outSQLTbl[i] if i+1 <= len(tbls) else get_filename(tlbs[i]),
            append=isAppend, api=api_db
        )
        
        RTBL.append(_rtbl)
    
    return RTBL[0] if len(RTBL) == 1 else RTBL

