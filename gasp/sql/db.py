"""
Deal with DBMS Databases
"""

def create_db(newdb, overwrite=True, api='psql', use_template=True):
    """
    Create Relational Database
    
    APIS Available:
    * psql;
    * sqlite;
    """
    
    if api == 'psql':
        from gasp.sql.c     import sqlcon
        from gasp.sql.i     import lst_db
        from gasp.cons.psql import con_psql

        conparam = con_psql()
    
        dbs = lst_db()
    
        con = sqlcon(None, sqlAPI='psql')
        cs = con.cursor()
    
        if newdb in dbs and overwrite:
            cs.execute("DROP DATABASE {};".format(newdb))
    
        cs.execute("CREATE DATABASE {}{};".format(
            newdb, " TEMPLATE={}".format(conparam["TEMPLATE"]) \
                if "TEMPLATE" in conparam and use_template else ""
            )
        )
    
        cs.close()
        con.close()
    
    elif api == 'sqlite':
        import os
        import sqlite3
        
        try:
            if os.path.exists(newdb) and overwrite:
                from gasp.pyt.oss import del_file
                del_file(newdb)
            
            conn = sqlite3.connect(newdb)
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

def drop_db(database):
    """
    Delete PostgreSQL database
    
    Return 0 if the database does not exist
    """
    
    from gasp.sql.c import sqlcon
    from gasp.sql.i import lst_db
    
    databases = lst_db()
    
    if database not in databases: return 0
    
    con = sqlcon(None, sqlAPI='psql')
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

    return 1


"""
Merge Databases
"""

def merge_dbs(destinationDb, dbs,
              tbls_to_merge=None, ignoreCols=None):
    """
    Put several database into one
    
    For now works only with PostgreSQL
    """
    
    import os
    from gasp.pyt.oss import fprop, del_file
    from gasp.sql     import psql_cmd
    from gasp.sql.i   import db_exists, lst_tbl
    from gasp.sql.db  import create_db, drop_db
    from gasp.sql.tbl import rename_tbl, tbls_to_tbl
    from gasp.sql.fm  import dump_tbls
    from gasp.sql.to  import restore_tbls
    from gasp.sql.tbl import distinct_to_table, del_tables
    
    # Prepare database
    fdb = fprop(destinationDb, ['fn', 'ff'])
    if os.path.isfile(destinationDb):
        if fdb['fileformat'] == '.sql':
            newdb = create_db(fdb['filename'], 
                overwrite=True, api='psql')
            
            psql_cmd(newdb, destinationDb)
            
            destinationDb = newdb
        
        else:
            raise ValueError((
                'destinationDb is a file but is not correct. The file must be'
                ' a SQL Script'
            ))
    
    else:
        # Check if destination db exists
        if not db_exists(destinationDb):
            create_db(destinationDb, overwrite=None, api='psql')
    
    # Check if dbs is a list or a dir
    if type(dbs) == list:
        dbs = dbs
    elif os.path.isdir(dbs):
        # list SQL files
        from gasp.pyt.oss import lst_ff
        
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
        DB_NAME = fprop(dbs[i], 'fn')
        create_db(DB_NAME, overwrite=True, api='psql')
        
        # Restore DB
        psql_cmd(DB_NAME, dbs[i])
        
        # List Tables
        if not tbls_to_merge:
            tbls__ = lst_tbl(DB_NAME, excludeViews=True, api='psql')
            tbls   = [t for t in tbls__ if t not in ignoreCols]
        else:
            tbls   = tbls_to_merge
        
        # Rename Tables
        newTbls = rename_tbl(DB_NAME, {tbl : "{}_{}".format(
            tbl, str(i)) for tbl in tbls})
        
        for t in range(len(tbls)):
            if tbls[t] not in TABLES:
                TABLES[tbls[t]] = ["{}_{}".format(tbls[t], str(i))]
            
            else:
                TABLES[tbls[t]].append("{}_{}".format(tbls[t], str(i)))
        
        # Dump Tables
        SQL_DUMP = os.path.join(
            os.path.dirname(dbs[i]), 'tbl_{}.sql'.format(DB_NAME)
        ); dump_tbls(DB_NAME, newTbls, SQL_DUMP)
        
        # Restore Tables in the destination Database
        restore_tbls(destinationDb, SQL_DUMP, newTbls)
        
        # Delete Temp Database
        drop_db(DB_NAME)
        
        # Delete SQL File
        del_file(SQL_DUMP)
    
    # Union of all tables
    max_len = max([len(TABLES[t]) for t in TABLES])
    
    for tbl in TABLES:
        # Rename original table
        NEW_TBL = "{}_{}".format(tbl, max_len)
        rename_tbl(destinationDb, {tbl : NEW_TBL})
        
        TABLES[tbl].append(NEW_TBL)
        
        # Union
        tbls_to_tbl(destinationDb, TABLES[tbl], tbl + '_tmp')
        
        # Group By
        distinct_to_table(destinationDb, tbl + '_tmp', tbl, cols=None)
        
        # Drop unwanted tables
        del_tables(destinationDb, TABLES[tbl] + [tbl + '_tmp'])
    
    return destinationDb

