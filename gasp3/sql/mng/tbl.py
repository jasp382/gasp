"""
Manage DBMS Tables
"""

def create_tbl(conParam, table, fields, orderFields=None, api='psql'):
    """
    Create Table in Database
    
    API's Available:
    * psql;
    * sqlite;
    """
    
    if api == 'psql':
        from gasp3.sql.c import psqlcon
    
        ordenedFields = orderFields if orderFields else fields.keys()
    
        con = psqlcon(conParam)
    
        cursor = con.cursor()
    
        cursor.execute(
            "CREATE TABLE {} ({})".format(
                table,
                ', '.join([
                    '{} {}'.format(
                        ordenedFields[x], fields[ordenedFields[x]]
                    ) for x in range(len(ordenedFields))
                ])
            )
        )
    
        con.commit()
    
        cursor.close()
        con.close()
    
    elif api == 'sqlite':
        import sqlite3
        
        conn = sqlite3.connect(conParam)
        cursor = conn.cursor()
        
        cursor.execute(
            "CREATE TABLE {} ({})".format(
                table,
                ', '.join([
                    "{} {}".format(k, fields[k]) for k in fields
                ])
            )
        )
        
        conn.commit()
        cursor.close()
        conn.close()
    
    return table


def new_view(sqliteDb, newView, q):
    """
    Create view in a SQLITE DB
    """
    
    conn = sqlite3.connect(sqliteDb)
    cs = conn.cursor()
    
    cs.execute("CREATE VIEW {} AS {}".format(newView, q))
    
    conn.commit()
    cs.close()
    conn.close()
    
    return newView


def rename_tbl(conParam, table, newName):
    """
    Rename PGSQL Table
    """
    
    from gasp3.sql.c import psqlcon
    
    con = psqlcon(conParam)
    
    cursor = con.cursor()
    
    cursor.execute(
        "ALTER TABLE {} RENAME TO {}".format(table, newName)
    )
    
    con.commit()
    
    cursor.close()
    con.close()
    
    return newName


"""
Delete Tables
"""

def del_tables(lnk, pg_table_s, isViews=None):
    """
    Delete all tables in pg_table_s
    """
    
    from gasp3       import goToList
    from gasp3.sql.c import psqlcon
    
    pg_table_s = goToList(pg_table_s)
        
    con = psqlcon(lnk)
    
    l = []
    for i in range(0, len(pg_table_s), 100):
        l.append(pg_table_s[i:i+100])
    
    for lt in l:
        cursor = con.cursor()
        cursor.execute('DROP {} IF EXISTS {};'.format(
            'TABLE' if not isViews else 'VIEW', ', '.join(lt)))
        con.commit()
        cursor.close()
    
    con.close()


def del_tables_wbasename(conParam, table_basename):
    """
    Delete all tables with a certain general name
    """
    
    pgTables = lst_tbl_basename(table_basename, conParam)
    
    del_tables(conParam, pgTables)


def drop_table_data(dic_con, table, where=None):
    """
    Delete all data on a PGSQL Table
    """
    
    from gasp3.sql.c import psqlcon
    
    con = psqlcon(dic_con)
    
    cursor = con.cursor()    
    
    cursor.execute("DELETE FROM {}{};".format(
        table, "" if not where else " WHERE {}".format(where)
    ))
    
    con.commit()
    cursor.close()
    con.close()


def drop_where_cols_are_same(conParam, table, colA, colB):
    """
    Delete rows Where colA has the same value than colB
    """
    
    from gasp.sql.c import psqlcon
    
    con = psqlcon(conParam)
    
    cursor = con.cursor()
    
    cursor.execute('DELETE FROM {} WHERE {}={}'.format(table, colA, colB))
    
    con.commit()
    cursor.close()
    con.close()


"""
Restore
"""
def dump_table(conParam, table, outsql):
    """
    Dump one table into a SQL File
    """
    
    from gasp3 import exec_cmd
    
    outcmd = exec_cmd((
        "pg_dump -Fc -U {user} -h {host} -p {port} "
        "-w -t {tbl} {db} > {out}"
    ).format(
        user=conParam["USER"], host=conParam["HOST"],
        port=conParam["PORT"], tbl=table,
        db=conParam["DATABASE"], out=outsql
    ))
    
    return outsql

def restore_table(conParam, sql, tablename):
    """
    Restore one table from a sql Script
    """
    
    from gasp3 import exec_cmd
    
    outcmd = exec_cmd((
        "pg_restore -U {user} -h {host} -p {port} "
        "-w -t {tbl} -d {db} {sqls}"
    ).format(
        user=conParam["USER"], host=conParam["HOST"],
        port=conParam["PORT"], tbl=tablename,
        db=conParam["DATABASE"], sqls=sql
    ))
    
    return tablename

"""
Write new tables or edit tables in Database
"""

def ntbl_by_query(lnk, outbl, query, ntblIsView=None, api='psql'):
    """
    Create table by query
    
    API's Available:
    * psql;
    * ogr2ogr
    """
    
    if api == 'psql':
        from gasp3.sql.c import psqlcon
    
        con = psqlcon(lnk)
    
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
        
        from gasp3 import exec_cmd
        
        cmd = (
            'ogr2ogr -update -append -f "SQLite" {db} -nln "{nt}" '
            '-dialect sqlite -sql "{q}" {db}' 
        ).format(
             db=lnk, nt=outbl, q=query
        )
        
        outcmd = exec_cmd(cmd)
    
    else:
        raise ValueError('API {} is not available!'.format(api))
    
    return outbl


"""
Merge Tables
"""

def tbls_to_tbl(conParam, lst_tables, outTable):
    """
    Append all tables in lst_tables into the outTable
    """
    
    sql = " UNION ALL ".join([
        "SELECT * FROM {}".format(t) for t in lst_tables])
    
    outTable = ntbl_by_query(conParam, outTable, sql, api='psql')
    
    return outTable
