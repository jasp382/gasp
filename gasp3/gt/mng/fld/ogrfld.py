"""
Manage OGR Fields
"""

def copy_flds(inLyr, outLyr, __filter=None):
    
    if __filter:
        __filter = [__filter] if type(__filter) != list else __filter
    
    inDefn = inLyr.GetLayerDefn()
    
    for i in range(0, inDefn.GetFieldCount()):
        fDefn = inDefn.GetFieldDefn(i)
        
        if __filter:
            if fDefn.name in __filter:
                outLyr.CreateField(fDefn)
            
            else:
                continue
        
        else:
            outLyr.CreateField(fDefn)
    
    del inDefn, fDefn


def add_fields_sqldialect(table, fields):
    """
    Add fields to table using SQL dialect
    """
    
    import os
    from gasp3 import exec_cmd
    
    tbl_name = os.path.splitext(os.path.basename(table))[0]
    
    if type(fields) != dict:
        raise ValueError('Fields argument should be a dict')
    
    ogrinfo = 'ogrinfo {i} -sql "{s}"'
    
    for fld in fields:
        sql = 'ALTER TABLE {tableName} ADD COLUMN {col} {_type};'.format(
            tableName = tbl_name, col=fld, _type=fields[fld]
        )
        
        outcmd = exec_cmd(ogrinfo.format(
            i=table, s=sql
        ))
