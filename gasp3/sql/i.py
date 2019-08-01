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
    
    from gasp3.dt.fm.sql import query_to_df
    
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
        from gasp3.dt.fm.sql import query_to_df
    
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


def lst_tbl_basename(basename, dic_con, schema='public'):
    """
    List tables with name that includes basename
    """
    
    from gasp3.sql.c import psqlcon
    
    conn = psqlcon(dic_con)
    
    cs = conn.cursor()
    cs.execute((
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema='{}' AND table_name LIKE '%{}%'".format(
            schema, basename
        )
    ))
    
    f = [x[0] for x in cs.fetchall()]
    
    cs.close()
    conn.close()
    
    return f


"""
Counting in table
"""

def row_num(conObj, table, where=None, api='psql'):
    """
    Return the number of rows in Query
    
    API's Available:
    * psql;
    * sqlite;
    """
    
    from gasp3.dt.fm.sql import query_to_df
    
    if not table.startswith('SELECT '):
        Q = "SELECT COUNT(*) AS nrows FROM {}{}".format(
            table,
            "" if not where else " WHERE {}".format(where)
        )
    else:
        Q = "SELECT COUNT(*) AS nrows FROM ({}) AS foo".format(table)
    
    d = query_to_df(conObj, Q, db_api=api)
    
    return int(d.iloc[0].nrows)


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


"""
Table Meta
"""

def check_last_id(lnk, pk, table):
    """
    Check last ID of a given table
    
    return 0 if there is no data
    
    TODO: Do this with Pandas
    """
    
    from gasp3.sql.c     import psqlcon
    from gasp3.dt.fm.sql import query_to_df
    
    q = "SELECT MAX({}) AS fid FROM {}".format(pk, table)
    d = query_to_df(lnk, q, db_api='psql').fid.tolist()
    
    if not d[0]:
        return 0
    else:
        return d[0]


"""
Geometric Properties
"""

def tbl_ext(conParam, table, geomCol):
    """
    Return extent of the geometries in one pgtable
    """
    
    from gasp.fm.sql import query_to_df
    
    q = (
        "SELECT MIN(ST_X(pnt_geom)) AS eleft, MAX(ST_X(pnt_geom)) AS eright, "
        "MIN(ST_Y(pnt_geom)) AS bottom, MAX(ST_Y(pnt_geom)) AS top "
        "FROM ("
            "SELECT (ST_DumpPoints({geomcol})).geom AS pnt_geom "
            "FROM {tbl}"
        ") AS foo"
    ).format(tbl=table, geomcol=geomCol)
    
    ext = query_to_df(conParam, q, db_api='psql').to_dict(orient='index')[0]
    
    return [
        ext['eleft'], ext['bottom'], ext['eright'], ext['top']
    ]

