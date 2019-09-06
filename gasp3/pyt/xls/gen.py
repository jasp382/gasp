"""
Manage Excel data
"""

def merge_xls_in_folder(tbl_folder, out_table):
    """
    Get all excel tables in a folder and make one table of them
    """
    
    import pandas
    from gasp3.pyt.oss import list_files
    from gasp3.dt.fm   import tbl_to_obj
    from gasp3.dt.to   import obj_to_tbl
    
    tables = list_files(tbl_folder, file_format=['.xls', '.xlsx'])
    
    dfs = [tbl_to_obj(table) for table in tables]
    
    result = pandas.concat(dfs)
    
    out_table = obj_to_tbl(result, out_table)
    
    return out_table


def sheets_into_file(xlsFolder, outXls, intSheets):
    """
    For each xls file in one folder, pick one interest sheet
    and save all sheets in a single file
    """
    
    from gasp3               import goToList
    from gasp3.pyt.oss       import list_files, get_filename
    from gasp3.pyt.xls.sheet import copy_sheet_to_file
    
    xls_s = list_files(xlsFolder, file_format=['.xls', '.xlsx'])
    
    for xlsPath in xls_s:
        copy_sheet_to_file(
            xlsPath, outXls, intSheets,
            {intSheets : get_filename(xlsPath, forceLower=True)}
        )
    
    return outXls