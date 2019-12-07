"""
Database data to Python Object/Array
"""

def Q_to_df(conParam, query, db_api='psql', geomCol=None, epsg=None):
    """
    Query database and convert data to Pandas Dataframe/GeoDataFrame
    
    API's Available:
    * psql;
    * sqlite;
    * mysql;
    """
    
    if not geomCol:
        import pandas
        from gasp3.sql.c import alchemy_engine
    
        pgengine = alchemy_engine(conParam, api=db_api)
    
        df = pandas.read_sql(query, pgengine, columns=None)
    
    else:
        from geopandas   import GeoDataFrame
        from gasp3.sql.c import sqlcon
        
        con = sqlcon(conParam)
        
        df = GeoDataFrame.from_postgis(
            query, con, geom_col=geomCol,
            crs="epsg:{}".format(str(epsg)) if epsg else None
        )
    
    return df


def tbl_to_dict(tbl, con, cols=None, apidb='psql'):
    """
    PG TABLE DATA to Python dict
    """
    
    from gasp3       import goToList
    from gasp3.sql.i import cols_name
    
    cols = cols_name(con, tbl) if not cols else \
        goToList(cols)
    
    data = Q_to_df(
        con,
        'SELECT {cols_} FROM {table}'.format(
            cols_=', '.join(["{t}.{c} AS {c}".format(
                t=tbl, c=i
            ) for i in cols]),
            table=tbl
        ), db_api=apidb
    ).to_dict(orient="records")
    
    return data


"""
Dump Databases and their tables
"""

def dump_db(conDB, outSQL, api='psql'):
    """
    DB to SQL Script
    """
    
    from gasp3 import exec_cmd
    
    if api == 'psql':
        cmd = "pg_dump -U {} -h {} -p {} -w {} > {}".format(
            conDB["USER"], conDB["HOST"], conDB["PORT"],
            conDB["DATABASE"], outSQL
        )
    
    elif api == 'mysql':
        cmd = (
            "mysqldump -u {} --port {} -p{} --host {} "
            "{} > {}"
        ).format(
            conDB["USER"], conDB["PORT"], conDB["PASSWORD"],
            conDB["HOST"], conDB["DATABASE"], outSQL
        )
    
    else:
        raise ValueError('{} API is not available'.format(api))
    
    outcmd = exec_cmd(cmd)
    
    return outSQL


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

