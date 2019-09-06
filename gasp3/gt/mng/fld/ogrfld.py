"""
Manage OGR Fields
"""
from osgeo import ogr

def add_fields(table, fields):
    """
    Receive a feature class and a dict with the field name and type
    and add the fields in the feature class
    
    TODO: Check if fields is a dict
    """
    
    import os
    
    if type(table) == ogr.Layer:
        lyr = table
        c = 0
    
    else:
        if os.path.exists(table) and os.path.isfile(table):
            # Open table in edition mode
            __table = ogr.GetDriverByName(
                drv_name(table)).Open(table, 1)
            
            # Get Layer
            lyr = __table.GetLayer()
            c=1 
        
        else:
            raise ValueError('File path does not exist')
    
    for fld in fields:
        lyr.CreateField(ogr.FieldDefn(fld, fields[fld]))
    
    if c:
        del lyr
        __table.Destroy()
    else:
        return lyr


def add_fields_to_tables(inFolder, fields, tbl_format='.shp'):
    """
    Add fields to several tables in a folder
    """
    
    from gasp3.pyt.oss import list_files
    
    tables = list_files(inFolder, file_format=tbl_format)
    
    for table in tables:
        add_fields(table, fields)


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

def rename_column(inShp, columns, output, api="ogr2ogr"):
    """
    Rename Columns in Shp
    
    TODO: For now implies output. In the future, it option will be removed
    """
    
    if api == "ogr2ogr":
        import os; from gasp3   import goToList
        from gasp3.pyt.oss      import get_filename
        from gasp3.gt.anls.exct import sel_by_attr
        
        # List Columns
        cols = lst_fld(inShp)
        for c in cols:
            if c in columns:
                continue
            else:
                columns[c] = c
        
        columns["geometry"] = "geometry"
        
        """
        # Rename original shp
        newFiles = rename_files_with_same_name(
            os.path.dirname(inShp), get_filename(inShp),
            get_filename(inShp) + "_xxx"
        )
        """
        
        # Rename columns by selecting data from input
        outShp = sel_by_attr(inShp, "SELECT {} FROM {}".format(
            ", ".join(["{} AS {}".format(c, columns[c]) for c in columns]),
            get_filename(inShp)
        ) , output, api_gis='ogr')
        
        # Delete tempfile
        #del_file(newFiles)
    
    else:
        raise ValueError("{} is not available".format(api))
    
    return outShp
