"""
Tools for DBMS and SQL
"""


def run_sql_script(lnk, database, sqlfile):
    """
    Run a sql file do whatever is on that script
    """
    
    from gasp import exec_cmd
    
    cmd = 'psql -h {} -U {} -p {} -w {} < {}'.format(
        lnk['HOST'], lnk['USER'], lnk['PORT'],
        database, sqlfile
    )
    
    outcmd = exec_cmd(cmd)
    
    return database

