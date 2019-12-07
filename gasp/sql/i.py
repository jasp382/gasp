""""
Get Information about SQL database or database data
"""

from gasp.sql.c import sqlcon

"""
Info about databases
"""

def list_db(conParam):
    """
    List all PostgreSQL databases
    """
    
    con = sqlcon(conParam)
    
    cursor = con.cursor()
    
    cursor.execute("SELECT datname FROM pg_database")
    
    return [d[0] for d in cursor.fetchall()]


def db_exists(lnk, db):
    """
    Database exists
    """
    con = sqlcon(lnk)
        
    cursor = con.cursor()
    
    cursor.execute("SELECT datname FROM pg_database")
    
    dbs = [d[0] for d in cursor.fetchall()]
    
    con.close()
    
    return 1 if db in dbs else 0


"""
Tables Info
"""

def lst_views(conParam, schema='public', basename=None):
    """
    List Views in database
    """
    
    from gasp.pyt    import obj_to_lst
    from gasp.sql.fm import q_to_obj
    
    basename = obj_to_lst(basename)
    
    basenameStr = "" if not basename else "{}".format(
        " OR ".join(["{} LIKE '%%{}%%'".format(
            "table_name", b
        ) for b in basename])
    )
    
    views = q_to_obj(conParam, (
        "SELECT table_name FROM information_schema.views "
        "WHERE table_schema='{}'{}"
    ).format(schema, "" if not basename else " AND ({})".format(
        basenameStr
    )), db_api='psql')
    
    return views.table_name.tolist()


def lst_tbl(conObj, schema='public', excludeViews=None, api='psql',
            basename=None):
    """
    list tables in a database
    
    API's Available:
    * psql;
    * sqlite;
    * mysql;
    """
    
    from gasp.pyt import obj_to_lst
    
    basename = obj_to_lst(basename)
    
    basenameStr = "" if not basename else "{}".format(
        " OR ".join(["{} LIKE '%%{}%%'".format(
            "table_name" if api == 'psql' else "name", b
        ) for b in basename])
    )
    
    if api == 'psql':
        from gasp.sql.fm import q_to_obj
        
        Q = (
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='{}'{}"
        ).format(schema, "" if not basename else " AND ({})".format(
            basenameStr))
    
        tbls = q_to_obj(conObj, Q, db_api='psql')
    
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
            "SELECT name FROM sqlite_master WHERE type='table'{};".format(
                "" if not basename else " AND ({})".format(basenameStr)
            )
        )
        
        __tbls = [n[0] for n in tables]
        cursor.close()
        conn.close()
    
    elif api == 'mysql':
        """
        List Tables in MySQL Database
        """
        
        from gasp.sql.c import alchemy_engine
        
        c = alchemy_engine(conObj, api='mysql')
        
        __tbls = c.table_names()
    
    else:
        raise ValueError('API {} is not available!'.format(api))
    
    return __tbls


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
    
    from gasp.sql.fm import q_to_obj
    
    if not table.startswith('SELECT '):
        Q = "SELECT COUNT(*) AS nrows FROM {}{}".format(
            table,
            "" if not where else " WHERE {}".format(where)
        )
    else:
        Q = "SELECT COUNT(*) AS nrows FROM ({}) AS foo".format(table)
    
    d = q_to_obj(conObj, Q, db_api=api)
    
    return int(d.iloc[0].nrows)


"""
Info about fields in table
"""

def cols_name(conparam, table, sanitizeSpecialWords=True, api='psql'):
    """
    Return the columns names of a table in one Database
    """
    
    if api == 'psql':
        c = sqlcon(conparam)
    
        cursor = c.cursor()
        cursor.execute("SELECT * FROM {} LIMIT 1;".format(table))
        colnames = [desc[0] for desc in cursor.description]
    
        if sanitizeSpecialWords:
            from gasp.cons.psql import PG_SPECIAL_WORDS
    
            for i in range(len(colnames)):
                if colnames[i] in PG_SPECIAL_WORDS:
                    colnames[i] = '"{}"'.format(colnames[i])
    
    elif api == 'sqlite':
        import sqlite3
        
        con = sqlite3.connect(conparam)
        
        cursor = con.execute("SELECT * FROM {} LIMIT 1".format(table))
        
        colnames = list(map(lambda x: x[0], cursor.description))
    
    elif api == 'mysql':
        from gasp.sql.fm import q_to_obj
        
        data = q_to_obj(
            conparam, "SELECT * FROM {} LIMIT 1".format(table), db_api='mysql')
        
        colnames = data.columns.values
    
    else:
        raise ValueError('API {} is not available'.format(api))
    
    return colnames


def cols_type(pgsqlDic, table, sanitizeColName=True, pyType=True):
    """
    Return columns names and types of a PostgreSQL table
    """
    
    from gasp.cons.psql import PG_SPECIAL_WORDS, map_psqltypes
    
    c = sqlcon(pgsqlDic)
    
    cursor = c.cursor()
    cursor.execute("SELECT * FROM {} LIMIT 50;".format(table))
    coltypes = {
        desc[0]: map_psqltypes(
            desc[1], python=pyType) for desc in cursor.description
    }
    
    if sanitizeColName:
        for name in coltypes:
            if name in PG_SPECIAL_WORDS:
                n = '"{}"'.format(name)
                coltypes[n] = coltypes[name]
                del coltypes[name]
    
    return coltypes


"""
Table Meta
"""

def check_last_id(lnk, pk, table):
    """
    Check last ID of a given table
    
    return 0 if there is no data
    """
    
    from gasp.sql.c  import sqlcon
    from gasp.sql.fm import q_to_obj
    
    q = "SELECT MAX({}) AS fid FROM {}".format(pk, table)
    d = q_to_obj(lnk, q, db_api='psql').fid.tolist()
    
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
    
    from gasp.sql.fm import q_to_obj
    
    q = (
        "SELECT MIN(ST_X(pnt_geom)) AS eleft, MAX(ST_X(pnt_geom)) AS eright, "
        "MIN(ST_Y(pnt_geom)) AS bottom, MAX(ST_Y(pnt_geom)) AS top "
        "FROM ("
            "SELECT (ST_DumpPoints({geomcol})).geom AS pnt_geom "
            "FROM {tbl}"
        ") AS foo"
    ).format(tbl=table, geomcol=geomCol)
    
    ext = q_to_obj(conParam, q, db_api='psql').to_dict(orient='index')[0]
    
    return [
        ext['eleft'], ext['bottom'], ext['eright'], ext['top']
    ]

