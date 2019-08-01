"""
Deal with DBMS Databases
"""

def create_db(lnk, newdb, overwrite=True, api='psql'):
    """
    Create Relational Database
    
    APIS Available:
    * psql;
    * sqlite;
    """
    
    if api == 'psql':
        from gasp3.sql.c import psqlcon
        from gasp3.sql.i import list_db
    
        dbs = list_db(lnk)
    
        con = psqlcon(lnk)
        cs = con.cursor()
    
        if newdb in dbs and overwrite:
            cs.execute("DROP DATABASE {};".format(newdb))
    
        cs.execute(
            "CREATE DATABASE {}{};".format(
                newdb,
                " TEMPLATE={}".format(lnk["TEMPLATE"]) \
                    if "TEMPLATE" in lnk else ""
            )
        )
    
        cs.close()
        con.close()
    
    elif api == 'sqlite':
        import os
        import sqlite3
        
        try:
            DB = os.path.join(lnk, newdb)
            if os.path.exists(DB) and overwrite:
                from gasp.oss.ops import del_file
                del_file(os.path.join(DB))
            
            conn = sqlite3.connect(DB)
        except Error as e:
            print(e)
        finally:
            conn.close()
    
    else:
        raise ValueError('API {} is not available'.format(api))
    
    return newdb


"""
Delete Databases
"""

def drop_db(lnk, database):
    """
    Delete PostgreSQL database
    
    Return 0 if the database does not exist
    """
    
    from gasp3.sql.c import psqlcon
    from gasp3.sql.i import list_db
    
    if "DATABASE" in lnk:
        raise ValueError(
            "For this method, the dict used to connected to "
            "PostgreSQL could not have a DATABASE key"
        )
    
    databases = list_db(lnk)
    
    if database not in databases: return 0
    
    con = psqlcon(lnk)
    cursor = con.cursor()
    
    cursor.execute("DROP DATABASE {};".format(database))
        
    cursor.close()
    con.close()

