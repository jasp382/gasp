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
        from gasp3.sql.c import sqlcon
    
        ordenedFields = orderFields if orderFields else fields.keys()
    
        con = sqlcon(conParam)
    
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


def rename_tbl(conParam, tblNames):
    """
    Rename PGSQL Table
    
    tblNames = {old_name: new_name, ...}
    """
    
    from gasp3.sql.c import sqlcon
    
    con = sqlcon(conParam)
    
    cursor = con.cursor()
    
    new_names =[]
    for k in tblNames:
        cursor.execute(
            "ALTER TABLE {} RENAME TO {}".format(k, tblNames[k])
        )
        new_names.append(tblNames[k])
    
    con.commit()
    
    cursor.close()
    con.close()
    
    return new_names[0] if len(new_names) == 1 else new_names


"""
Delete Tables
"""

def del_tables(lnk, pg_table_s, isViews=None):
    """
    Delete all tables in pg_table_s
    """
    
    from gasp3       import goToList
    from gasp3.sql.c import sqlcon
    
    pg_table_s = goToList(pg_table_s)
        
    con = sqlcon(lnk)
    
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
    
    from gasp3.sql.c import sqlcon
    
    con = sqlcon(dic_con)
    
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
    
    from gasp3.sql.c import sqlcon
    
    con = sqlcon(conParam)
    
    cursor = con.cursor()
    
    cursor.execute('DELETE FROM {} WHERE {}={}'.format(table, colA, colB))
    
    con.commit()
    cursor.close()
    con.close()


"""
Restore
"""
def dump_tbls(conParam, tables, outsql, startWith=None):
    """
    Dump one table into a SQL File
    """
    
    from gasp3 import exec_cmd, goToList
    
    tbls = goToList(tables)
    
    if startWith:
        from gasp3.sql.i import lst_tbl
        
        db_tbls = lst_tbl(conParam, api='psql')
        
        dtbls = []
        for t in db_tbls:
            for b in tbls:
                if t.startswith(b):
                    dtbls.append(t)
        
        tbls = dtbls
    
    outcmd = exec_cmd((
        "pg_dump -Fc -U {user} -h {host} -p {port} "
        "-w {tbl} {db} > {out}"
    ).format(
        user=conParam["USER"], host=conParam["HOST"],
        port=conParam["PORT"], db=conParam["DATABASE"], out=outsql,
        tbl=" ".join(["-t {}".format(t) for t in tbls])
    ))
    
    return outsql


def restore_tbls(conParam, sql, tablenames=None):
    """
    Restore one table from a sql Script
    """
    
    from gasp3 import exec_cmd, goToList
    
    tbls = goToList(tablenames)
    
    tblStr = "" if not tablenames else " {}".format(" ".join([
        "-t {}".format(t) for t in tbls]))
    
    outcmd = exec_cmd((
        "pg_restore -U {user} -h {host} -p {port} "
        "-w{tbl} -d {db} {sqls}"
    ).format(
        user=conParam["USER"], host=conParam["HOST"],
        port=conParam["PORT"], db=conParam["DATABASE"], sqls=sql, tbl=tblStr
    ))
    
    return tablenames

"""
Write new tables or edit tables in Database
"""

def q_to_ntbl(lnk, outbl, query, ntblIsView=None, api='psql'):
    """
    Create table by query
    
    API's Available:
    * psql;
    * ogr2ogr
    """
    
    if api == 'psql':
        from gasp3.sql.c import sqlcon
    
        con = sqlcon(lnk)
    
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


def exec_write_q(conDB, queries, api='psql'):
    """
    Execute Queries and save result in the database
    """
    
    from gasp3 import goToList
    
    qs = goToList(queries)
    
    if not qs:
        raise ValueError("queries value is not valid")
    
    if api == 'psql':
        from gasp3.sql.c import sqlcon
        
        con = sqlcon(conDB)
    
        cs = con.cursor()
    
        for q in qs:
            cs.execute(q)
    
        con.commit()
        cs.close()
        con.close()
    
    elif api == 'sqlite':
        import sqlite3
        
        con = sqlite3.connect(conDB)
        cs  = con.cursor()
        
        for q in qs:
            cs.execute(q)
        
        con.commit()
        cs.close()
        con.close()
    
    else:
        raise ValueError('API {} is not available'.format(api))


def update_table(con_pgsql, pg_table, dic_new_values, dic_ref_values=None, 
                 logic_operator='OR'):
    """
    Update Values on a PostgreSQL table

    new_values and ref_values are dict with fields as keys and values as 
    keys values.
    If the values (ref and new) are strings, they must be inside ''
    e.g.
    dic_new_values = {field: '\'value\''}
    """
    
    from gasp3.sql.c import sqlcon

    __logic_operator = ' OR ' if logic_operator == 'OR' else ' AND ' \
        if logic_operator == 'AND' else None

    if not __logic_operator:
        raise ValueError((
            'Defined operator is not valid.\n '
            'The valid options are \'OR\' and \'AND\'')
        )

    con = sqlcon(con_pgsql)

    cursor = con.cursor()
    
    if dic_ref_values:
        whrLst = []
        for x in dic_ref_values:
            if dic_ref_values[x] == 'NULL':
                whrLst.append('{} IS NULL'.format(x))
            else:
                whrLst.append('{}={}'.format(x, dic_ref_values[x]))
        
        whr = " WHERE {}".format(__logic_operator.join(whrLst))
    
    else:
        whr = ""

    update_query = "UPDATE {tbl} SET {pair_new}{where};".format(
        tbl=pg_table,
        pair_new=",".join(["{fld}={v}".format(
            fld=x, v=dic_new_values[x]) for x in dic_new_values]),
        where = whr
    )

    cursor.execute(update_query)

    con.commit()
    cursor.close()
    con.close()


def update_query(db, table, new_values, wherePairs, whrLogic="OR"):
    """
    Update SQLITE Table
    """
    
    import sqlite3
    
    conn = sqlite3.connect(db)
    cs   = conn.cursor()
    
    LOGIC_OPERATOR = " OR " if whrLogic == "OR" else " AND " \
        if whrLogic == "AND" else None
    
    if not LOGIC_OPERATOR:
        raise ValueError("whrLogic value is not valid")
    
    Q = "UPDATE {} SET {} WHERE {}".format(
        table, ", ".join(["{}={}".format(
            k, new_values[k]) for k in new_values
        ]),
        LOGIC_OPERATOR.join(["{}={}".format(
            k, wherePairs[k]) for k in wherePairs
        ])
    )
    
    cs.execute(Q)
    
    conn.commit()
    cs.close()
    conn.close()
    

def set_values_use_pndref(sqliteDB, table, colToUpdate,
                        pndDf, valCol, whrCol, newCol=None):
    """
    Update Column based on conditions
    
    Add distinct values in pndCol in sqliteCol using other column as Where
    """
    
    import sqlite3
    
    conn = sqlite3.connect(sqliteDB)
    cs   = conn.cursor()
    
    if newCol:
        cs.execute("ALTER TABLE {} ADD COLUMN {} integer".format(
            table, colToUpdate
        ))
    
    VALUES = pndDf[valCol].unique()
    
    for val in VALUES:
        filterDf = pndDf[pndDf[valCol] == val]
        
        cs.execute("UPDATE {} SET {}={} WHERE {}".format(
            table, colToUpdate, val,
            str(filterDf[whrCol].str.cat(sep=" OR "))
        ))
    
    conn.commit()
    cs.close()
    conn.close()


def replace_null_with_other_col_value(con_pgsql, pgtable, nullFld, replaceFld):
    """
    Do the following
    
    Convert the next table:
    FID | COL1 | COL2
     0  |  1   | -99
     1  |  2   | -99
     2  | NULL | -88
     3  | NULL | -87
     4  |  7   | -99
     5  |  9   | -99
     
    Into:
    FID | COL1 | COL2
     0  |  1   | -99
     1  |  2   | -99
     2  | -88  | -88
     3  | -87  | -87
     4  |  7   | -99
     5  |  9   | -99
    """
    
    from gasp3.sql.c import sqlcon
    
    con = sqlcon(con_pgsql)
    
    cursor = con.cursor()
    
    cursor.execute(
        "UPDATE {t} SET {nullF}=COALESCE({repF}) WHERE {nullF} IS NULL".format(
            t=pgtable, nullF=nullFld, repF=replaceFld
        )
    )
    
    con.commit()
    cursor.close()
    con.close()


def distinct_to_table(lnk, pgtable, outable, cols=None):
    """
    Distinct values of one column to a new table
    """
    
    from gasp3       import goToList
    from gasp3.sql.c import sqlcon
    
    cols = goToList(cols)
    
    if not cols:
        from gasp3.sql.i import cols_name
        
        cols = cols_name(lnk, pgtable, api='psql')
    
    con = sqlcon(lnk)
    
    cs = con.cursor()
    
    cs.execute(
        "CREATE TABLE {nt} AS SELECT {cls} FROM {t} GROUP BY {cls}".format(
            nt=outable, cls=', '.join(cols),
            t=pgtable
        )
    )
    
    con.commit()
    cs.close()
    con.close()
    
    return outable


"""
Merge Tables
"""

def tbls_to_tbl(conParam, lst_tables, outTable):
    """
    Append all tables in lst_tables into the outTable
    """
    
    sql = " UNION ALL ".join([
        "SELECT * FROM {}".format(t) for t in lst_tables])
    
    outTable = q_to_ntbl(conParam, outTable, sql, api='psql')
    
    return outTable
