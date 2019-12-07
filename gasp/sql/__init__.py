"""
Tools for DBMS and SQL
"""


def psql_cmd(lnk, sqlfile):
    """
    Run a sql file do whatever is on that script
    """
    
    import os
    from gasp import exec_cmd

    if os.path.isdir(sqlfile):
        from gasp.pyt.oss import lst_ff

        sqls = lst_ff(sqlfile, file_format='.sql')
    else:
        sqls = [sqlfile]
    
    cmd = 'psql -h {} -U {} -p {} -w {} < {}'
    
    for s in sqls:
        outcmd = exec_cmd(cmd.format(
            lnk['HOST'], lnk['USER'], lnk['PORT'],
            lnk["DATABASE"], s
        ))
    
    return lnk["DATABASE"]

