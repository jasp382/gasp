"""
Database data to Python Object/Array
"""

def query_to_df(conParam, query, db_api='psql'):
    """
    Query database and convert data to Pandas Dataframe
    
    API's Available:
    * psql;
    * sqlite;
    """
    
    import pandas
    from gasp3.sql.c import alchemy_engine
    
    pgengine = alchemy_engine(conParam, api=db_api)
    
    df = pandas.read_sql(query, pgengine, columns=None)
    
    return df


def tbl_to_dict(tbl, con, cols=None, apidb='psql'):
    """
    PG TABLE DATA to Python dict
    """
    
    from gasp3       import goToList
    from gasp3.sql.i import cols_name
    
    cols = cols_name(con, tbl) if not cols else \
        goToList(cols)
    
    data = query_to_df(
        con,
        'SELECT {cols_} FROM {table}'.format(
            cols_=', '.join(cols),
            table=tbl
        ), db_api=apidb
    ).to_dict(orient="records")
    
    return data


def psql_to_geodf(conParam, query, geomCol='geom',
                    epsg=None):
    """
    Query database and convert data to Pandas GeoDataframe
    """
    
    from geopandas   import GeoDataFrame
    from gasp3.sql.c import psqlcon
    
    con = psqlcon(conParam)
    
    df = GeoDataFrame.from_postgis(
        query, con, geom_col=geomCol,
        crs="epsg:{}".format(str(epsg)) if epsg else None
    )
    
    return df

