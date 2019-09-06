"""
Manage fields
"""

from gasp3.sql.c       import psqlcon
from gasp3.sql.mng.tbl import q_to_ntbl


"""
Operations
"""
def add_field(lnk, pgtable, columns):
    """
    Add new field to a table
    """
    
    # Verify is columns is a dict
    if type(columns) != dict:
        raise ValueError(
            'columns should be a dict (name as keys; field type as values)'
        )
    
    con = psqlcon(lnk)
    
    cursor = con.cursor()
    
    cursor.execute(
        "ALTER TABLE {} ADD {};".format(
            pgtable,
            ", ".join(["{} {}".format(x, columns[x]) for x in columns])
        )
    )
    
    con.commit()
    cursor.close()
    con.close()


def drop_column(lnk, pg_table, columns):
    """
    Delete column from pg_table
    """
    
    from gasp3 import goToList
    
    con = psqlcon(lnk)
    
    cursor = con.cursor()
    
    columns = goToList(columns)
    
    cursor.execute('ALTER TABLE {} {};'.format(
        pg_table, ', '.join(['DROP COLUMN {}'.format(x) for x in columns])
    ))
    
    con.commit()
    cursor.close()
    con.close()


def change_field_type(lnk, table, fields, outable,
                        cols=None):
    """
    Imagine a table with numeric data saved as text. This method convert
    that numeric data to a numeric field.
    
    fields = {'field_name' : 'field_type'}
    """
    
    if not cols:
        cols = cols_name(lnk, table)
    
    else:
        from gasp3 import goToList
        
        cols = goToList(cols)
    
    select_fields = [f for f in cols if f not in fields]
    
    con = psqlcon(lnk)
    
    # Create new table with the new field with converted values
    cursor = con.cursor()
    
    cursor.execute((
        'CREATE TABLE {} AS SELECT {}, {} FROM {}'
    ).format(
        outable,
        ', '.join(select_fields),
        ', '.join(['CAST({f_} AS {t}) AS {f_}'.format(
            f_=f, t=fields[f]) for f in fields
        ]),
        table
    ))
    
    con.commit()
    cursor.close()
    con.close()


def split_column_value_into_columns(lnkPgsql, table, column, splitChar,
                                    new_cols, new_table):
    """
    Split column value into several columns
    """
    
    if type(new_cols) != list:
        raise ValueError(
            'new_cols should be a list'
        )
    
    nr_cols = len(new_cols)
    
    if nr_cols < 2:
        raise ValueError(
            'new_cols should have 2 or more elements'
        )
    
    # Get columns types from table
    tblCols = cols_name(lnkPgsql, table)
    
    # SQL construction
    SQL = "SELECT {}, {} FROM {}".format(
        ", ".join(tblCols),
        ", ".join([
            "split_part({}, '{}', {}) AS {}".format(
                column, splitChar, i+1, new_cols[i]
            ) for i in range(len(new_cols))
        ]),
        table
    )
    
    q_to_ntbl(lnkPgsql, new_table, SQL, api='psql')
    
    return new_table


def text_columns_to_column(conParam, inTable, columns, strSep, newCol, outTable=None):
    """
    Several text columns to a single column
    """
    
    from gasp3 import goToList
    
    mergeCols = goToList(columns)
    
    tblCols = cols_type(
        conParam, inTable, sanitizeColName=None, pyType=False)
    
    for col in mergeCols:
        if tblCols[col] != 'text' and tblCols[col] != 'varchar':
            raise ValueError('{} should be of type text'.format(col))
    
    coalesce = ""
    for i in range(len(mergeCols)):
        if not i:
            coalesce += "COALESCE({}, '')".format(mergeCols[i])
        
        else:
            coalesce += " || '{}' || COALESCE({}, '')".format(
                strSep, mergeCols[i])
    
    
    if outTable:
        # Write new table
        colsToSelect = [_c for _c in tblCols if _c not in mergeCols]
        
        if not colsToSelect:
            sel = coalesce + " AS {}".format(newCol)
        else:
            sel = "{}, {}".format(
                ", ".join(colsToSelect), coalesce + " AS {}".format(newCol)
            )
        
        q_to_ntbl(
            conParam, outTable, "SELECT {} FROM {}".format(sel, inTable),
            api='psql'
        )
        
        return outTable
    
    else:
        # Add column to inTable
        from gasp3.sql.mng.tbl import update_table
        
        add_field(conParam, inTable, {newCol : 'text'})
        
        update_table(
            conParam, inTable, {newCol : coalesce}
        )
        
        return inTable


def columns_to_timestamp(conParam, inTbl, dayCol, hourCol, minCol, secCol, newTimeCol,
                         outTbl, selColumns=None, whr=None):
    
    """
    Columns to timestamp column
    """
    
    from gasp3 import goToList
    
    selCols = goToList(selColumns)
    
    sql = (
        "SELECT {C}, TO_TIMESTAMP("
            "COALESCE(CAST({day} AS text), '') || ' ' || "
            "COALESCE(CAST({hor} AS text), '') || ':' || "
            "COALESCE(CAST({min} AS text), '') || ':' || "
            "COALESCE(CAST({sec} AS text), ''), 'YYYY-MM-DD HH24:MI:SS'"
        ") AS {TC} FROM {T}{W}"
    ).format(
        C   = "*" if not selCols else ", ".join(selCols),
        day = dayCol, hor=hourCol, min=minCol, sec=secCol,
        TC  = newTimeCol, T=inTbl,
        W   = "" if not whr else " WHERE {}".format(whr)
    )
    
    q_to_ntbl(conParam, outTbl, sql, api='psql')
    
    return outTbl


def trim_char_in_col(conParam, pgtable, cols, trim_str, outTable,
                     onlyTrailing=None, onlyLeading=None):
    """
    Python implementation of the TRIM PSQL Function
    
    The PostgreSQL trim function is used to remove spaces or set of
    characters from the leading or trailing or both side from a string.
    """
    
    from gasp3 import goToList
    
    cols = goToList(cols)
    
    colsTypes = cols_type(conParam, pgtable,
                                 sanitizeColName=None, pyType=False)
    
    for col in cols:
        if colsTypes[col] != 'text' and colsTypes[col] != 'varchar':
            raise ValueError('{} should be of type text'.format(col))
    
    colsToSelect = [_c for _c in colsTypes if _c not in cols]
    
    tail_lead_str = "" if not onlyTrailing and not onlyLeading else \
        "TRAILING " if onlyTrailing and not onlyLeading else \
        "LEADING " if not onlyTrailing and onlyLeading else ""
    
    trimCols = [
        "TRIM({tol}{char} FROM {c}) AS {c}".format(
            c=col, tol=tail_lead_str, char=trim_str
        ) for col in cols
    ]
    
    if not colsToSelect:
        cols_to_select = "{}".format(", ".join(trimCols))
    else:
        cols_to_select = "{}, {}".format(
            ", ".join(colsToSelect), ", ".join(colsReplace)
        )
    
    q_to_ntbl(conParam, outTable,
        "SELECT {} FROM {}".format(colsToSelect, pgtable), api='psql'
    )


def replace_char_in_col(conParam, pgtable, cols, match_str, replace_str, outTable):
    """
    Replace char in all columns in cols for the value of replace_str
    
    Python implementation of the REPLACE PSQL Function
    """
    
    from gasp3 import goToList
    
    cols = goToList(cols)
    
    colsTypes = cols_type(conParam, pgtable,
                                 sanitizeColName=None, pyType=False)
    
    for col in cols:
        if colsTypes[col] != 'text' and colsTypes[col] != 'varchar':
            raise ValueError('{} should be of type text'.format(col))
    
    colsToSelect = [_c for _c in colsTypes if _c not in cols]
    
    colsReplace  = [
        "REPLACE({c}, '{char}', '{nchar}') AS {c}".format(
            c=col, char=match_str, nchar=replace_str
        ) for col in cols
    ]
    
    if not colsToSelect:
        cols_to_select = "{}".format(", ".join(colsReplace))
    else:
        cols_to_select = "{}, {}".format(
            ", ".join(colsToSelect), ", ".join(colsReplace))
    
    q_to_ntbl(conParam, outTable,
        "SELECT {cols} FROM {tbl}".format(
            cols  = cols_to_select,
            tbl   = pgtable
        ), api='psql'
    )
    
    return outTable


def substring_to_newfield(conParam, table, field, newCol,
                          idxFrom, idxTo):
    """
    Get substring of string by range
    """
    
    from gasp3.sql.mng.tbl import exec_write_q
    
    # Add new field to table
    add_field(conParam, table, {newCol : "text"})
    
    # Update table
    exec_write_q(conParam, (
        "UPDATE {tbl} SET {nf} = substring({f} from {frm} for {to}) "
        "WHERE {nf} IS NULL"
    ).format(
        tbl=table, nf=newCol, f=field, frm=idxFrom,
        to=idxTo
    ), api='psql')
    
    return table


def add_geomtype_to_col(conParam, table, newCol, geomCol):
    """
    Add Geom Type to Column
    """
    
    from gasp3.sql.mng.tbl import exec_write_q
    
    # Add new field to table
    add_field(conParam, table, {newCol : "text"})
    
    exec_write_q(conParam, "UPDATE {} SET {} = ST_GeometryType({})".format(
        table, newCol, geomCol
    ), api='psql')
    
    return table

