""""
Get Information about SQL database or database data
"""

from gasp3.sql.c import psqlcon

"""
Info about databases
"""

def list_db(conParam):
    """
    List all PostgreSQL databases
    """
    
    con = psqlcon(conParam)
    
    cursor = con.cursor()
    
    cursor.execute("SELECT datname FROM pg_database")
    
    return [d[0] for d in cursor.fetchall()]


def db_exists(lnk, db):
    """
    Database exists
    """
    con = psqlcon(lnk)
        
    cursor = con.cursor()
    
    cursor.execute("SELECT datname FROM pg_database")
    
    dbs = [d[0] for d in cursor.fetchall()]
    
    return 1 if db in dbs else 0


"""
Tables Info
"""

def lst_views(conParam, schema='public'):
    """
    List Views in database
    """
    
    from gasp.fm.sql import query_to_df
    
    views = query_to_df(conParam, (
        "SELECT table_name FROM information_schema.views "
        "WHERE table_schema='{}'"
    ).format(schema), db_api='psql')
    
    return views.table_name.tolist()


def lst_tbl(conObj, schema='public', excludeViews=None, api='psql'):
    """
    list tables in a database
    
    API's Available:
    * psql;
    * sqlite;
    """
    
    if api == 'psql':
        from gasp.fm.sql import query_to_df
    
        tbls = query_to_df(conObj, (
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='{}'"
        ).format(schema), db_api='psql')
    
        if excludeViews:
            views = lst_views(conObj, schema=schema)
        
            __tbls = [i for i in tbls.table_name.tolist() if i not in views]
    
        else:
            __tbls = tbls.table_name.tolist()
    
    elif api == 'sqlite':
        """
        List tables in one sqliteDB
        """
        
        import sqlite3
        
        conn = sqlite3.connect(conObj)
        cursor = conn.cursor()
        
        tables = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table';"
        )
        
        __tbls = [n[0] for n in tables]
        cursor.close()
        conn.close()    
    
    else:
        raise ValueError('API {} is not available!'.format(api))
    
    return __tbls


"""
Info about fields in table
"""

def cols_name(conparam, table, sanitizeSpecialWords=True, api='psql'):
    """
    Return the columns names of a table in one Database
    """
    
    if api == 'psql':
        c = psqlcon(conparam)
    
        cursor = c.cursor()
        cursor.execute("SELECT * FROM {} LIMIT 50;".format(table))
        colnames = [desc[0] for desc in cursor.description]
    
        if sanitizeSpecialWords:
            from gasp3.cons.psql import special_words
            # Prepare one wayout for special words
            special_words = special_words()
    
            for i in range(len(colnames)):
                if colnames[i] in special_words:
                    colnames[i] = '"{}"'.format(colnames[i])
    
    elif api == 'sqlite':
        import sqlite3
        
        con = sqlite3.connect(conparam)
        
        cursor = con.execute("SELECT * FROM {}".format(table))
        
        colnames = list(map(lambda x: x[0], cursor.description))
    
    else:
        raise ValueError('API {} is not available'.format(api))
    
    return colnames

