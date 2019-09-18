"""
Field Management Utils
"""

def add_filename_to_field(tables, new_field, table_format='.dbf'):
    """
    Update a table with the filename in a new field
    """
    
    from gasp3.pyt.oss import lst_ff
    from .ogrfld       import add_fields
    
    if os.path.isdir(tables):
        __tables = lst_ff(tables, file_format=table_format)
    
    else:
        __tables = [tables]
    
    for table in __tables:
        add_fields(table, {new_field: 'varchar(50)'})
        
        name_tbl = os.path.splitext(os.path.basename(table))[0]
        name_tbl = name_tbl.lower() if name_tbl.isupper() else name_tbl
        update_table(
            table,
            {new_field: name_tbl}
        )

