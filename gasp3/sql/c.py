"""
Connect to Databases
"""


def psqlcon(conParam):
    """
    Connect to PostgreSQL Database
    
    example - conParam = {
        "HOST" : "localhost", "USER" : "postgres",
        "PORT" : "5432", "PASSWORD" : "admin",
        "DATABASE" : "db_name"
    }
    """
    
    import psycopg2
    
    try:
        if "DATABASE" not in conParam:
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
            c = psycopg2.connect(
                user=conParam["USER"], password=conParam["PASSWORD"],
                host=conParam["HOST"], port=conParam["PORT"]
            )
            c.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    
        else:
            c = psycopg2.connect(
                database=conParam["DATABASE"], user=conParam["USER"],
                password=conParam["PASSWORD"], host=conParam["HOST"],
                port=conParam["PORT"],
            )
        
        return c
    
    except psycopg2.Error as e:
        raise ValueError(str(e))


def alchemy_engine(conParam, api='psql'):
    """
    SQLAlchemy Enignes
    """
    
    from sqlalchemy import create_engine
    
    if api == 'psql':
        """
        Get engine that could be used for pandas to import data into
        PostgreSQL
        """
    
        return create_engine(
            'postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}'.format(
                user=conParam["USER"], password=conParam["PASSWORD"],
                host=conParam["HOST"], port=conParam["PORT"],
                db=conParam["DATABASE"]
            )
        )
    
    elif api == 'sqlite':
        """
        Return Alchemy Engine for SQLITE
        """
        
        from gasp.oss   import os_name
        
        if os_name() == 'Windows':
            constr = r'sqlite:///{}'.format(conParam)
        else:
            constr = 'sqlite:///{}'.format(conParam)
    
        return create_engine(constr)
    
    else:
        raise ValueError('API {} is not available!'.format(api))

