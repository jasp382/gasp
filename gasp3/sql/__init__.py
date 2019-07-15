"""
Tools for DBMS and SQL
"""

def psql_special_words():
    return ['table', 'column', 'natural', 'group', 'left', 'right', 'order']

def run_sql_script(lnk, database, sqlfile):
    """
    Run a sql file do whatever is on that script
    """
    
    from gasp3 import exec_cmd
    
    cmd = 'psql -h {host} -U {usr} -p {port} -w {db} < {sql_script}'.format(
        host = lnk['HOST'], usr = lnk['USER'], port = lnk['PORT'],
        db  = database    , sql_script = sqlfile
    )
    
    outcmd = exec_cmd(cmd)

