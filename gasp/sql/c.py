"""
Connect to Databases
"""


def sqlcon(db, sqlAPI='psql'):
    """
    Connect to PostgreSQL Database
    """
    
    if sqlAPI == 'psql':
        import psycopg2
        from gasp.cons.psql import con_psql

        conparam = con_psql()
    
        try:
            if not db:
                from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
                c = psycopg2.connect(
                    user=conparam["USER"], password=conparam["PASSWORD"],
                    host=conparam["HOST"], port=conparam["PORT"]
                )
                c.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    
            else:
                c = psycopg2.connect(
                    database=db, user=conparam["USER"],
                    password=conparam["PASSWORD"], host=conparam["HOST"],
                    port=conparam["PORT"],
                )
        
            return c
    
        except psycopg2.Error as e:
            raise ValueError(str(e))
    
    elif sqlAPI == 'mysql':
        import mysql.connector
        from gasp.cons.mysql import con_mysql

        conparam = con_mysql()
        
        c = mysql.connector.connect(
            user=conparam["USER"], password=conparam["PASSWORD"],
            host=conparam["HOST"], database=db,
            port=conparam["PORT"]
        )
        
        return c
    
    else:
        raise ValueError("{} API is not available".format(sqlAPI))


def alchemy_engine(db, api='psql'):
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

        from gasp.cons.psql import con_psql

        conparam = con_psql()
    
        return create_engine(
            'postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}'.format(
                user=conparam["USER"], password=conparam["PASSWORD"],
                host=conparam["HOST"], port=conparam["PORT"],
                db=db
            )
        )
    
    elif api == 'sqlite':
        """
        Return Alchemy Engine for SQLITE
        """
        
        from gasp.pyt.oss import os_name
        
        if os_name() == 'Windows':
            constr = r'sqlite:///{}'.format(db)
        else:
            constr = 'sqlite:///{}'.format(db)
    
        return create_engine(constr)
    
    elif api == 'mysql':
        """
        Return MySQL Engine
        """

        from gasp.cons.mysql import con_mysql

        conparam = con_mysql()
        
        return create_engine('mysql://{usr}:{pw}@{host}/{db}'.format(
            usr=conparam['USER'], pw=conparam["PASSWORD"],
            host=conparam['HOST'], db=db
        ))
    
    else:
        raise ValueError('API {} is not available!'.format(api))

