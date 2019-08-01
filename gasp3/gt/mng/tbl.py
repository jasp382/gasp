"""
Using Tables
"""

def update_tbl(table, new_values, ref_values=None):
    """
    Update a feature class table with new values
    
    Where with OR condition
    new_values and ref_values are dict with fields as keys and values as 
    keys values.
    """
    
    import os
    from gasp3 import exec_cmd
    
    if ref_values:
        update_query = 'UPDATE {tbl} SET {pair_new} WHERE {pair_ref};'.format(
            tbl=os.path.splitext(os.path.basename(table))[0],
            pair_new=','.join(["{fld}={v}".format(
                fld=x, v=new_values[x]) for x in new_values]),
            pair_ref=' OR '.join(["{fld}='{v}'".format(
                fld=x, v=ref_values[x]) for x in ref_values])
        )
    
    else:
        update_query = 'UPDATE {tbl} SET {pair};'.format(
            tbl=os.path.splitext(os.path.basename(table))[0],
            pair=','.join(["{fld}={v}".format(
                fld=x, v=new_values[x]) for x in new_values])
        )
    
    ogrinfo = 'ogrinfo {i} -dialect sqlite -sql "{s}"'.format(
        i=table, s=update_query
    )
    
    # Run command
    outcmd = exec_cmd(ogrinfo)
