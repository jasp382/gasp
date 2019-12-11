"""
Deal with DBMS Databases
"""

def create_db(lnk, newdb, overwrite=True, api='psql'):
    """
    Create Relational Database
    
    APIS Available:
    * psql;
    * sqlite;
    """
    
    if api == 'psql':
        from gasp3.sql.c import sqlcon
        from gasp3.sql.i import list_db
    
        dbs = list_db(lnk)
    
        con = sqlcon(lnk)
        cs = con.cursor()
    
        if newdb in dbs and overwrite:
            cs.execute("DROP DATABASE {};".format(newdb))
    
        cs.execute(
            "CREATE DATABASE {}{};".format(
                newdb,
                " TEMPLATE={}".format(lnk["TEMPLATE"]) \
                    if "TEMPLATE" in lnk else ""
            )
        )
    
        cs.close()
        con.close()
    
    elif api == 'sqlite':
        import os
        import sqlite3
        
        try:
            DB = os.path.join(lnk, newdb)
            if os.path.exists(DB) and overwrite:
                from gasp3.pyt.oss import del_file
                del_file(os.path.join(DB))
            
            conn = sqlite3.connect(DB)
        except Error as e:
            print(e)
        finally:
            conn.close()
    
    else:
        raise ValueError('API {} is not available'.format(api))
    
    return newdb


"""
Delete Databases
"""

def drop_db(lnk, database):
    """
    Delete PostgreSQL database
    
    Return 0 if the database does not exist
    """
    
    from gasp3.sql.c import sqlcon
    from gasp3.sql.i import list_db
    
    if "DATABASE" in lnk:
        raise ValueError(
            "For this method, the dict used to connected to "
            "PostgreSQL could not have a DATABASE key"
        )
    
    databases = list_db(lnk)
    
    if database not in databases: return 0
    
    con = sqlcon(lnk)
    cursor = con.cursor()
    
    try:
        cursor.execute("DROP DATABASE {};".format(database))
    except:
        cursor.execute((
            "SELECT pg_terminate_backend(pg_stat_activity.pid) "
            "FROM pg_stat_activity "
            "WHERE pg_stat_activity.datname = '{}';"
        ).format(database))
        
        cursor.execute("DROP DATABASE {};".format(database))
        
    cursor.close()
    con.close()


"""
Merge Databases
"""

def merge_dbs(conPSQL, destinationDb, dbs,
              tbls_to_merge=None, ignoreCols=None):
    """
    Put several database into one
    
    For now works only with PostgreSQL
    """
    
    import os
    from gasp3.pyt.oss     import get_filename, del_file, get_fileformat
    from gasp3.sql         import run_sql_script
    from gasp3.sql.i       import db_exists, lst_tbl
    from gasp3.sql.mng.db  import create_db, drop_db
    from gasp3.sql.mng.tbl import rename_tbl, tbls_to_tbl
    from gasp3.sql.fm      import dump_tbls
    from gasp3.sql.to      import restore_tbls
    from gasp3.sql.mng.tbl import distinct_to_table, del_tables
    
    # Prepare database
    if os.path.isfile(destinationDb):
        if get_fileformat(destinationDb) == '.sql':
            newdb = create_db(
                conPSQL, get_filename(destinationDb),
                overwrite=True, api='psql'
            )
            
            run_sql_script(conPSQL, newdb, destinationDb)
            
            destinationDb = newdb
        
        else:
            raise ValueError((
                'destinationDb is a file but is not correct. The file must be'
                ' a SQL Script'
            ))
    
    else:
        # Check if destination db exists
        if not db_exists(conPSQL, destinationDb):
            create_db(conPSQL, destinationDb, overwrite=None, api='psql')
    
    # Check if dbs is a list or a dir
    if type(dbs) == list:
        dbs = dbs
    elif os.path.isdir(dbs):
        # list SQL files
        from gasp3.pyt.oss import lst_ff
        
        dbs = lst_ff(dbs, file_format='.sql')
    
    else:
        raise ValueError(
            '''
            dbs value should be a list with paths 
            to sql files or a dir with sql files inside
            '''
        )
    
    TABLES = {}
    
    for i in range(len(dbs)):
        # Create DB
        DB_NAME = get_filename(dbs[i])
        create_db(conPSQL, DB_NAME, overwrite=True, api='psql')
        
        # Restore DB
        run_sql_script(conPSQL, DB_NAME, dbs[i])
        
        # List Tables
        conPSQL["DATABASE"] = DB_NAME
        if not tbls_to_merge:
            tbls__ = lst_tbl(conPSQL, excludeViews=True, api='psql')
            tbls   = [t for t in tbls__ if t not in ignoreCols]
        else:
            tbls   = tbls_to_merge
        
        # Rename Tables
        newTbls = rename_tbl(conPSQL, {tbl : "{}_{}".format(
            tbl, str(i)) for tbl in tbls})
        
        for t in range(len(tbls)):
            if tbls[t] not in TABLES:
                TABLES[tbls[t]] = ["{}_{}".format(tlbs[t], str(i))]
            
            else:
                TABLES[tbls[t]].append("{}_{}".format(tbls[t], str(i)))
        
        # Dump Tables
        SQL_DUMP = os.path.join(
            os.path.dirname(dbs[i]), 'tbl_{}.sql'.format(DB_NAME)
        ); dump_tbls(conPSQL, newTbls, SQL_DUMP)
        
        conPSQL["DATABASE"] = destinationDb
        
        # Restore Tables in the destination Database
        restore_tbls(conPSQL, SQL_DUMP, newTbls)
        
        # Delete Temp Database
        del conPSQL["DATABASE"]
        drop_db(conPSQL, DB_NAME)
        
        # Delete SQL File
        del_file(SQL_DUMP)
    
    # Union of all tables
    conPSQL["DATABASE"] = destinationDb
    
    max_len = max([len(TABLES[t]) for t in TABLES])
    
    for tbl in TABLES:
        # Rename original table
        NEW_TBL = "{}_{}".format(tbl, max_len)
        rename_tbl(conPSQL, {tbl : NEW_TBL})
        
        TABLES[tbl].append(NEW_TBL)
        
        # Union
        tbls_to_tbl(conPSQL, TABLES[tbl], tbl + '_tmp')
        
        # Group By
        distinct_to_table(conPSQL, tbl + '_tmp', tbl, cols=None)
        
        # Drop unwanted tables
        del_tables(conPSQL, TABLES[tbl] + [tbl + '_tmp'])
    
    return destinationDb

