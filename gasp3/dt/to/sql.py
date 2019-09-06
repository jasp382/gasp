"""
Data to a Relational Database
"""

def psql_insert_query(dic_pgsql, query, execute_many_data=None):
    """
    Insert data into a PGSQL Table
    """
    
    from gasp3.sql.c     import connection
    from psycopg2.extras import execute_values
    
    con = psqlcon(dic_pgsql)
    
    cursor = con.cursor()
    if execute_many_data:
        execute_values(cursor, query, execute_many_data)
    
    else:
        cursor.execute(query)
    
    con.commit()
    cursor.close()
    con.close()


def sqlite_insert_query(db, table, cols, new_values, execute_many=None):
    """
    Method to insert data into SQLITE Database
    """
    
    import sqlite3
    from gasp3 import goToList
    
    cols = goToList(cols)
    
    if not cols:
        raise ValueError('cols value is not valid')
    
    conn = sqlite3.connect(db)
    cs = conn.cursor()
    
    if not execute_many:
        cs.execute(
            "INSERT INTO {} ({}) VALUES {}".join(
                table, ', '.join(cols),
                ', '.join(
                    ['({})'.format(', '.join(row)) for row in new_values]
                )
            )
        )
    
    else:
        cs.executemany(
            '''INSERT INTO {} ({}) VALUES ({})'''.format(
                table, ', '.join(cols),
                ', '.join(['?' for i in range(len(cols))])
            ),
            new_values
        )
    
    conn.commit()
    cs.close()
    conn.close()



def shp_to_psql(con_param, shpData, srsEpsgCode, pgTable=None, api="pandas"):
    """
    Send Shapefile to PostgreSQL
    
    if api is equal to "pandas" - GeoPandas API will be used;
    if api is equal to "shp2pgsql" - shp2pgsql tool will be used.
    """
    
    import os
    from gasp3.pyt.oss import get_filename
    
    if api == "pandas":
        from gasp3.dt.fm        import tbl_to_obj
        from gasp3.gt.prop.feat import get_gtype
    
    elif api == "shp2pgsql":
        from gasp3         import exec_cmd
        from gasp3.sql     import run_sql_script
        from gasp3.pyt.oss import del_file
    
    else:
        raise ValueError(
            'api value is not valid. options are: pandas and shp2pgsql'
        )
    
    # Check if shp is folder
    if os.path.isdir(shpData):
        from gasp3.pyt.oss import list_files
        
        shapes = list_files(shpData, file_format='.shp')
    
    else:
        from gasp3 import goToList
        
        shapes = goToList(shpData)
    
    tables = []
    for _i in range(len(shapes)):
        # Get Table name
        tname = get_filename(shapes[_i], forceLower=True) if not pgTable else \
            pgTable[_i] if type(pgTable) == list else pgTable
        
        # Import data
        if api == "pandas":
            # SHP to DataFrame
            df = tbl_to_obj(shapes[_i])
            
            df.rename(columns={
                x : x.lower() for x in df.columns.values
            }, inplace=True)
            
            if "geometry" in df.columns.values:
                geomCol = "geometry"
            
            elif "geom" in df.columns.values:
                geomCol = "geom"
            
            else:
                print(df.columns.values)
                raise ValuError("No Geometry found in shp")
            
            # GeoDataFrame to PSQL
            geodf_to_pgsql(
                con_param, df, tname, srsEpsgCode,
                get_gtype(shapes[_i], name=True, py_cls=False, gisApi='ogr'),
                colGeom=geomCol
            )
        
        else:
            sql_script = os.path.join(
                os.path.dirname(shapes[_i]), tname + '.sql'
            )
            
            cmd = (
                'shp2pgsql -I -s {epsg} -W UTF-8 '
                '{shp} public.{name} > {out}'
            ).format(
                epsg=srsEpsgCode, shp=shapes[_i], name=tname, out=sql_script
            )
            
            outcmd = exec_cmd(cmd)
            
            run_sql_file(con_param, con_param["DATABASE"], sql_script)
            
            del_file(sql_script)
        
        tables.append(tname)
    
    return tables[0] if len(tables) == 1 else tables


def shps_to_onepsql(folder_shp, epsg, conParam, out_table):
    """
    Send all shps to PGSQL and merge the data into a single table
    """
    
    from gasp3.sql.mng.tbl import tbls_to_tbl, del_tables
    
    pgTables = shp_to_psql(
        conParam, folder_shp, epsg, api="shp2pgsql"
    )
    
    tbls_to_tbl(conParam, pgTables, out_table)
    
    del_tables(conParam, pgTables)
    
    return out_table


def rst_to_psql(rst, srs, lnk={
        'HOST': 'localhost', 'PORT': '5432',
        'PASSWORD': 'admin', 'USER': 'postgres',
        'DATABASE': 'shogun_db'}, sql_script=None):
    """
    Run raster2pgsql to import a raster dataset into PostGIS Database
    """
    
    import os
    from gasp3     import exec_cmd
    from gasp3.sql import run_sql_script
    
    rst_name = os.path.splitext(os.path.basename(rst))[0]
    
    if not sql_script:
        sql_script = os.path.join(os.path.dirname(rst), rst_name + '.sql')
    
    cmd = (
        'raster2pgsql -s {epsg} -I -C -M {rfile} -F -t 100x100 '
        'public.{name} > {sqls}'
    ).format(
        epsg=str(srs), rfile=rst, name=rst_name, sqls=sql_script
    )
    
    run_sql_script(lnk, lnk["DATABASE"], sql_script)
    
    return rst_name


def txts_to_db(folder, conDB, delimiter, __encoding='utf-8', apidb='psql',
               dbIsNew=None, rewrite=None, toDBViaPandas=True):
    """
    Executes tbl_to_db for every file in a given folder
    
    The file name will be the table name
    """
    
    from gasp3.pyt.oss import list_files, get_filename
    
    if dbIsNew:
        # Create database
        from gasp3.sql.mng.db import create_db
        
        if api == 'psql':
            __con = {
                'HOST' : conDB["HOST"], 'PORT' : conDB["PORT"],
                'USER' : conDB["USER"], 'PASSWORD' : conDB["PASSWORD"]
            }
            
            DB = conDB["DATABASE"]
        
        else:
            import os
            __con = os.path.dirname(conDB)
            DB = os.path.basename(conDB)
        
        create_db(__con, DB, api=apidb, overwrite=rewrite)
    
    __files = list_files(folder, file_format=['.txt', '.csv', '.tsv'])
    
    if toDBViaPandas:
        """
        Send data to DB using Pandas
        """
        for __file in __files:
            tbl_to_db(
                __file, conDB, get_filename(__file),
                delimiter=delimiter, encoding_=__encoding, api_db=apidb
            )
    
    else:
        """
        Send data to DB using regular Python API
        """
        
        from gasp3.sql.mng.fld import pgtypes_from_pnddf
        from gasp3.sql.mng.tbl import create_tbl
        from gasp3.dt.fm       import tbl_to_obj
        
        # Get Table data
        table_data = {get_filename(f) : tbl_to_obj(
            f, _delimiter=delimiter, encoding_=__encoding
        ) for f in __files}
        
        
        if apidb == 'psql':
            # Create Tables
            dicColsT = {}
            for table in table_data:
                cols = list(table_data[table].columns)
            
                colsT = pgtypes_from_pnddf(table_data[table])
                dicColsT[table] = colsT
            
                create_tbl(conDB, table, colsT, orderFields=cols)
            
            # Insert data into tables
            for table in table_data:
                cols = list(table_data[table].columns)
                
                tableDf = table_data[table]
                
                for i in range(len(cols)):
                    if not i:
                        if dicColsT[table][cols[i]] == "text":
                            tableDf["row"] = u"('" + \
                                tableDf[cols[i]].astype(unicode) + u"'"
                        
                        else:
                            tableDf["row"] = u"(" + \
                                tableDf[cols[i]].astype(unicode)
                    
                    else:
                        if dicColsT[table][cols[i]] == "text":
                            tableDf["row"] = tableDf["row"] + u", '" + \
                                tableDf[cols[i]].astype(unicode) + u"'"
                        
                        else:
                            tableDf["row"] = tableDf["row"] + u", " + \
                                tableDf[cols[i]].astype(unicode)
                
                str_a = tableDf["row"].str.cat(sep=u"), ") + u")"
                sql = u"INSERT INTO {} ({}) VALUES {}".format(
                    unicode(table, 'utf-8'), u", ".join(cols), str_a
                )
                
                psql_insert_query(conDB, sql)
        else:
            raise ValueError("API {} is not available".format(apidb))

