"""
Connect to Databases
"""


def sqlcon(conParam, sqlAPI='psql'):
    """
    Connect to PostgreSQL Database
    
    example - conParam = {
        "HOST" : "localhost", "USER" : "postgres",
        "PORT" : "5432", "PASSWORD" : "admin",
        "DATABASE" : "db_name"
    }
    """
    
    if sqlAPI == 'psql':
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
    
    elif sqlAPI == 'mysql':
        import mysql.connector
        
        
        c = mysql.connector.connect(
            user=conParam["USER"], password=conParam["PASSWORD"],
            host=conParam["HOST"], database=conParam["DATABASE"],
            port=conParam["PORT"]
        )
        
        return c
    
    else:
        raise ValueError("{} API is not available".format(sqlAPI))


def alchemy_engine(conParam, api='psql'):
    """
    SQLAlchemy Enignes
    
    API's available:
    * psql;
    * sqlite;
    * mysql;
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
        
        from gasp3.pyt.oss import os_name
        
        if os_name() == 'Windows':
            constr = r'sqlite:///{}'.format(conParam)
        else:
            constr = 'sqlite:///{}'.format(conParam)
    
        return create_engine(constr)
    
    elif api == 'mysql':
        """
        Return MySQL Engine
        """
        
        return create_engine('mysql://{usr}:{pw}@{host}/{db}'.format(
            usr=conParam['USER'], pw=conParam["PASSWORD"],
            host=conParam['HOST'], db=conParam["DATABASE"]
        ))
    
    else:
        raise ValueError('API {} is not available!'.format(api))

