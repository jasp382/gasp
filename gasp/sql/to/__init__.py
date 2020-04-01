"""
Data to a Relational Database
"""


def restore_db(conDB, sqlScript, api='psql'):
    """
    Restore Database using SQL Script
    
    TODO: add mysql option
    """
    
    from gasp import exec_cmd
    
    if api == 'psql':
        cmd = 'psql -h {} -U {} -p {} -w {} < {}'.format(
            conDB['HOST'], conDB['USER'], conDB['PORT'],
            conDB["DATABASE"], sqlScript
        )
    
    elif api == 'mysql':
        cmd = 'mysql -u {} -p{} {} < {}'.format(
            conDB['USER'], conDB['PASSWORD'], conDB["DATABASE"],
            sqlScript
        )
    else:
        raise ValueError('{} API is not available'.format(api))
    
    outcmd = exec_cmd(cmd)
    
    return conDB["DATABASE"]


def restore_tbls(dbn, sql, tablenames=None):
    """
    Restore one table from a sql Script
    
    TODO: add mysql option
    """
    
    from gasp           import exec_cmd
    from gasp.cons.psql import con_psql
    from gasp.pyt       import obj_to_lst

    condb = con_psql()
    
    tbls = obj_to_lst(tablenames)
    
    tblStr = "" if not tablenames else " {}".format(" ".join([
        "-t {}".format(t) for t in tbls]))
    
    outcmd = exec_cmd((
        "pg_restore -U {user} -h {host} -p {port} "
        "-w{tbl} -d {db} {sqls}"
    ).format(
        user=condb["USER"], host=condb["HOST"],
        port=condb["PORT"], db=dbn, sqls=sql, tbl=tblStr
    ))
    
    return tablenames

###############################################################################
###############################################################################

def q_to_ntbl(db, outbl, query, ntblIsView=None, api='psql'):
    """
    Create table by query
    
    API's Available:
    * psql;
    * ogr2ogr
    """
    
    if api == 'psql':
        from gasp.sql.c import sqlcon
    
        con = sqlcon(db)
    
        curs = con.cursor()
    
        _q = "CREATE {} {} AS {}".format(
            "TABLE" if not ntblIsView else "VIEW",
            outbl, query
        )
    
        curs.execute(_q)
    
        con.commit()
        curs.close()
        con.close()
    
    elif api == 'ogr2ogr':
        """
        Execute a SQL Query in a SQLITE Database and store the result in the
        same database. Uses OGR2OGR instead of the regular SQLITE API
        """
        
        from gasp import exec_cmd
        
        cmd = (
            'ogr2ogr -update -append -f "SQLite" {db} -nln "{nt}" '
            '-dialect sqlite -sql "{q}" {db}' 
        ).format(
             db=db, nt=outbl, q=query
        )
        
        outcmd = exec_cmd(cmd)
    
    else:
        raise ValueError('API {} is not available!'.format(api))
    
    return outbl

###############################################################################
###############################################################################


def df_to_db(db, df, table, append=None, api='psql',
             epsg=None, geomType=None, colGeom='geometry'):
    """
    Pandas Dataframe/GeoDataFrame to PGSQL table
    
    API options:
    * psql;
    * sqlite
    """
    
    if api != 'psql' and api != 'sqlite':
        raise ValueError('API {} is not available'.format(api))
    
    from gasp.sql.c import alchemy_engine
    
    pgengine = alchemy_engine(db, api=api)
    
    if epsg and geomType:
        from geoalchemy2 import Geometry, WKTElement

        newdf = df.copy()
        
        newdf["geom"] = newdf[colGeom].apply(
            lambda x : WKTElement(x.wkt, srid=epsg)
        )
        
        if colGeom != 'geom':
            newdf.drop(colGeom, axis=1, inplace=True)
        
        newdf.to_sql(
            table, pgengine,
            if_exists='replace' if not append else 'append',
            index=False, dtype={"geom" : Geometry(geomType, srid=epsg)}
        )
    
    else:
        df.to_sql(
            table, pgengine,
            if_exists='replace' if not append else 'append',
            index=False
        )
    
    return table


def tbl_to_db(tblFile, db, sqlTbl, delimiter=None, encoding_='utf-8',
              sheet=None, isAppend=None, api_db='psql', colsMap=None):
    """
    Table file to Database Table
    
    API's available:
    * psql;
    * sqlite;
    """
    
    import os
    from gasp.pyt     import obj_to_lst
    from gasp.pyt.oss import fprop
    from gasp.fm      import tbl_to_obj
    
    if os.path.isdir(tblFile):
        from gasp.pyt.oss import lst_ff
        
        tbls = lst_ff(tblFile)
    
    else:
        tbls = obj_to_lst(tblFile)
    
    outSQLTbl = obj_to_lst(sqlTbl)
    
    RTBL = []
    for i in range(len(tbls)):
        fp = fprop(tbls[i], ['fn', 'ff'])
        ff = fp['fileformat']
        fn = fp['filename']
    
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
            raise ValueError('{} is not a valid table format!'.format(ff))
        
        if colsMap:
            data.rename(columns=colsMap, inplace=True)
    
        # Send data to database
        _rtbl = df_to_db(
            db, data,
            outSQLTbl[i] if i+1 <= len(tbls) else fn,
            append=isAppend, api=api_db
        )
        
        RTBL.append(_rtbl)
    
    return RTBL[0] if len(RTBL) == 1 else RTBL


def db_to_db(db_a, db_b, typeDBA, typeDBB):
    """
    All tables in one Database to other database
    
    Useful when we want to migrate a SQLITE DB to a PostgreSQL DB
    
    typesDB options:
    * sqlite
    * psql
    """
    
    import os
    from gasp.sql.fm import q_to_obj
    from gasp.sql.i  import lst_tbl
    from gasp.sql.db import create_db
    
    # List Tables in DB A
    tbls = lst_tbl(db_a, excludeViews=True, api=typeDBA)
    
    # Create database B
    db_b = create_db(db_b, overwrite=False, api=typeDBB)
    
    # Table to Database B
    for tbl in tbls:
        df = q_to_obj(
            db_a, "SELECT * FROM {}".format(tbl), db_api=typeDBA
        )
        
        df_to_db(db_b, df, tbl, append=None, api=typeDBB)


def tbl_fromdb_todb(from_db, to_db, tables, qForTbl=None, api='pandas'):
    """
    Send PGSQL Tables from one database to other
    """
    
    from gasp.pyt import obj_to_lst
    
    api = 'pandas' if api != 'pandas' and api != 'psql' else api
    
    tables = obj_to_lst(tables)
    
    if api == 'pandas':
        from gasp.sql.fm import q_to_obj
    
        for table in tables:
            if not qForTbl:
                tblDf = q_to_obj(from_db, "SELECT * FROM {}".format(
                    table), db_api='psql')
        
            else:
                if table not in qForTbl:
                    tblDf = q_to_obj(from_db, "SELECT * FROM {}".format(
                        table), db_api='psql')
            
                else:
                    tblDf = q_to_obj(from_db, qForTbl[table], db_api='psql')
        
            df_to_db(to_db, tblDf, table, api='psql')
    
    else:
        import os
        from gasp.pyt.oss import mkdir, del_folder
        from gasp.sql.fm  import dump_tbls
        from gasp.sql.to  import restore_tbls
        
        tmpFolder = mkdir(
            os.path.dirname(os.path.abspath(__file__)), randName=True
        )
        
        # Dump 
        sqlScript = dump_tbls(from_db, tables, os.path.join(
            tmpFolder, "tables_data.sql"
        ))
            
        # Restore
        restore_tbls(to_db, sqlScript, tables)
        
        del_folder(tmpFolder)


def apndtbl_in_otherdb(db_a, db_b, tblA, tblB, mapCols,
                       geomCol=None, srsEpsg=None):
    """
    Append data of one table to another table in other database.
    """
    
    from gasp.sql.fm import q_to_obj
    
    if geomCol and srsEpsg:
        df = q_to_obj(db_a, "SELECT {} FROM {}".format(
            ", ".join(list(mapCols.keys())), tblA
        ), db_api='psql', geomCol=geomCol, epsg=srsEpsg)
    
    else:
        df = q_to_obj(db_b, "SELECT {} FROM {}".format(
            ", ".join(list(mapCols.keys())), tblA
        ), db_api='psql', geomCol=None, epsg=None)
    
    # Change Names
    df.rename(columns=mapCols, inplace=True)
    
    if geomCol:
        for k in mapCols:
            if geomCol == k:
                geomCol = mapCols[k]
                break
    
    # Get Geom Type
    # Send data to other database
    if geomCol and srsEpsg:
        from gasp.gt.prop.feat import get_gtype
        
        gType = get_gtype(df, geomCol=geomCol, gisApi='pandas')
        
        df_to_db(
            db_b, df, tblB, append=True, api='psql', epsg=srsEpsg,
            geomType=gType, colGeom=geomCol
        )
    
    else:
        df_to_db(db_b, df, tblB, append=True, api='psql')
    
    return tblB


def rst_to_psql(rst, srs, dbname, sql_script=None):
    """
    Run raster2pgsql to import a raster dataset into PostGIS Database
    """
    
    import os
    from gasp     import exec_cmd
    from gasp.sql import psql_cmd
    
    rst_name = os.path.splitext(os.path.basename(rst))[0]
    
    if not sql_script:
        sql_script = os.path.join(os.path.dirname(rst), rst_name + '.sql')
    
    cmd = exec_cmd((
        'raster2pgsql -s {epsg} -I -C -M {rfile} -F -t 100x100 '
        'public.{name} > {sqls}'
    ).format(
        epsg=str(srs), rfile=rst, name=rst_name, sqls=sql_script
    ))
    
    psql_cmd(dbname, sql_script)
    
    return rst_name


def txts_to_db(folder, db, delimiter, __encoding='utf-8', apidb='psql',
               rewrite=None):
    """
    Executes tbl_to_db for every file in a given folder
    
    The file name will be the table name
    """
    
    from gasp.pyt.oss import lst_ff, fprop
    from gasp.sql.i   import db_exists
    
    if not db_exists(db):
        # Create database
        from gasp.sql.db import create_db
        
        create_db(db, api=apidb, overwrite=None)
    
    else:
        if rewrite:
            from gasp.sql.db import create_db
            create_db(db, api=db, overwrite=True)
    
    __files = lst_ff(folder, file_format=['.txt', '.csv', '.tsv'])
    
    """
    Send data to DB using Pandas
    """
    for __file in __files:
        tbl_to_db(
            __file, db, fprop(__file, 'fn'),
            delimiter=delimiter, encoding_=__encoding, api_db=apidb
        )


"""
OSM Related
"""

def osm_to_pgsql(osmXml, osmdb):
    """
    Use GDAL to import osmfile into PostGIS database
    """
    
    from gasp           import exec_cmd
    from gasp.cons.psql import con_psql
    from gasp.sql.i     import db_exists

    is_db = db_exists(osmdb)

    if not is_db:
        from gasp.sql.db import create_db

        create_db(osmdb, api='psql')

    con = con_psql()
    
    cmd = (
        "ogr2ogr -f PostgreSQL \"PG:dbname='{}' host='{}' port='{}' "
        "user='{}' password='{}'\" {} -lco COLUM_TYPES=other_tags=hstore"
    ).format(
        osmdb, con["HOST"], con["PORT"],
        con["USER"], con["PASSWORD"], osmXml
    )
    
    cmdout = exec_cmd(cmd)
    
    return osmdb

