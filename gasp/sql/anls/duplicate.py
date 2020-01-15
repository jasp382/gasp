"""
Use duplicates in tables
"""


def show_duplicates_in_xls(conParam, table, pkCols, outFile,
                           tableIsQuery=None):
    """
    Find duplicates and write these objects in a table
    """
    
    import pandas
    from gasp.pyt    import obj_to_lst
    from gasp.sql.fm import Q_to_df
    from gasp.to     import obj_to_tbl
    
    pkCols = obj_to_lst(pkCols)
    
    if not pkCols:
        raise ValueError("pkCols value is not valid")
    
    if not tableIsQuery:
        q = (
            "SELECT {t}.* FROM {t} INNER JOIN ("
                "SELECT {cls}, COUNT({cnt}) AS conta FROM {t} "
                "GROUP BY {cls}"
            ") AS foo ON {rel} "
            "WHERE conta > 1"
        ).format(
            t=table, cls=", ".join(pkCols), cnt=pkCols[0],
            rel=" AND ".join([
                "{t}.{c} = foo.{c}".format(t=table, c=col) for col in pkCols
            ])
        )
    
    else:
        q = (
            "SELECT foo.* FROM ({q_}) AS foo INNER JOIN ("
                "SELECT {cls}, COUNT({cnt}) AS conta "
                "FROM ({q_}) AS foo2 GROUP BY {cls}"
            ") AS jt ON {rel} "
            "WHERE conta > 1" 
        ).format(
            q_=table, cls=", ".join(pkCols), cnt=pkCols[0],
            rel=" AND ".join([
                "foo.{c} = jt.{c}".format(c=x) for x in pkCols
            ])
        )
    
    data = Q_to_df(conParam, q, db_api='psql')
    
    obj_to_tbl(data, outFile)
    
    return outFile
