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

