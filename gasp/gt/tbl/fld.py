"""
Fields
"""


def add_fields(tbl, fields, lyrN=1, api='ogr'):
    """
    Receive a feature class and a dict with the field name and type
    and add the fields in the feature class

    API Options:
    * ogr;
    * ogrinfo;
    * pygrass;
    * grass;

    For pygrass and grass field options are:
    * VARCHAR()
    * INT
    * DOUBLE PRECISION
    * DATE
    """

    if type(fields) != dict:
        raise ValueError('Fields argument should be a dict')

    import os

    if api == 'ogr':
        from osgeo import ogr
        from gasp.gt.prop.ff import drv_name
        from gasp.g.lyr.fld  import fields_to_lyr

        if os.path.exists(tbl) and os.path.isfile(tbl):
            # Open table in edition mode
            __table = ogr.GetDriverByName(drv_name(
                tbl)).Open(tbl, 1)
            
            # Get Layer
            lyr = __table.GetLayer()

            # Add fields to layer
            lyr = fields_to_lyr(lyr, fields)

            del lyr
            __table.Destroy()
        
        else:
            raise ValueError('File path does not exist')
    
    elif api == 'ogrinfo':
        from gasp         import exec_cmd
        from gasp.pyt.oss import fprop

        tname = fprop(tbl, 'fn')

        ogrinfo = 'ogrinfo {i} -sql "{s}"'

        for fld in fields:
            sql = 'ALTER TABLE {} ADD COLUMN {} {};'.format(
                tname, fld, fields[fld]
            )

            outcmd = exec_cmd(ogrinfo.format(i=tbl, s=sql))
    
    elif api == 'grass':
        from gasp import exec_cmd

        for fld in fields:
            rcmd = exec_cmd((
                "v.db.addcolumn map={} layer={} columns=\"{} {}\" --quiet"
            ).format(tbl, lyrN, fld, fields[fld]))
    
    elif api == 'pygrass':
        from grass.pygrass.modules import Module

        for fld in fields:
            c = Module(
                "v.db.addcolumn", map=tbl, layer=lyrN,
                columns='{} {}'.format(fld, fields[fld]),
                run_=False, quiet=True
            )

            c()
    
    else:
        raise ValueError('API {} is not available'.format(api))


def fields_to_tbls(inFolder, fields, tbl_format='.shp'):
    """
    Add fields to several tables in a folder
    """
    
    from gasp.pyt.oss import lst_ff
    
    tables = lst_ff(inFolder, file_format=tbl_format)
    
    for table in tables:
        add_fields(table, fields, api='ogr')


def del_cols(lyr, cols, api='grass', lyrn=1):
    """
    Remove Columns from Tables
    """

    from gasp.pyt import obj_to_lst

    cols = obj_to_lst(cols)

    if api == 'grass':
        from gasp import exec_cmd

        rcmd = exec_cmd((
            "v.db.dropcolumn map={} layer={} columns={} "
            "--quiet"
        ).format(
            lyr, str(lyrn), ','.join(cols)
        ))
    
    elif api == 'pygrass':
        from grass.pygrass.modules import Module

        m = Module(
            "v.db.dropcolumn", map=lyr, layer=lyrn,
            columns=cols, quiet=True, run_=True
        )
    
    else:
        raise ValueError("API {} is not available".format(api))

    return lyr


def rn_cols(inShp, columns, api="ogr2ogr"):
    """
    Rename Columns in Shp

    api options:
    * ogr2ogr;
    * grass;
    * pygrass;
    """
    
    if api == "ogr2ogr":
        import os
        from gasp.pyt         import obj_to_lst
        from gasp.pyt.oss     import fprop
        from gasp.pyt.oss     import del_file, lst_ff
        from gasp.gt.attr     import sel_by_attr
        from gasp.gt.prop.fld import lst_cols
        
        # List Columns
        cols = lst_cols(inShp)
        for c in cols:
            if c in columns:
                continue
            else:
                columns[c] = c
        
        columns["geometry"] = "geometry"

        # Get inShp Folder
        inshpfld = os.path.dirname(inShp)

        # Get inShp Filename and format
        inshpname = fprop(inShp, 'fn')

        # Temporary output
        output = os.path.join(inshpfld, inshpname + '_xtmp.shp')
        
        # Rename columns by selecting data from input
        outShp = sel_by_attr(inShp, "SELECT {} FROM {}".format(
            ", ".join(["{} AS {}".format(c, columns[c]) for c in columns]),
            inshpname
        ) , output, api_gis='ogr')
        
        # Delete Original file
        infiles = lst_ff(inshpfld, filename=inshpname)
        del_file(infiles)
        
        # Rename Output file
        oufiles = lst_ff(inshpfld, filename=inshpname + '_xtmp')
        for f in oufiles:
            os.rename(f, os.path.join(inshpfld, inshpname + fprop(f, 'ff')))
    
    elif api == 'grass':
        from gasp import exec_cmd

        for col in columns:
            rcmd = exec_cmd((
                "v.db.renamecolumn map={} layer=1 column={},{}"
            ).format(inShp, col, columns[col]))
    
    elif api == 'pygrass':
        from grass.pygrass.modules import Module

        for col in columns:
            func = Module(
                "v.db.renamecolumn", map=inShp,
                column="{},{}".format(col, columns[col]),
                quiet=True, run_=False
            )
            func()
    
    else:
        raise ValueError("{} is not available".format(api))
    
    return inShp


"""
Update data in Table Field
"""

def update_cols(table, new_values, ref_values=None):
    """
    Update a feature class table with new values
    
    Where with OR condition
    new_values and ref_values are dict with fields as keys and values as 
    keys values.
    """
    
    import os
    from gasp import exec_cmd
    
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


def filename_to_col(tables, new_field, table_format='.dbf'):
    """
    Update a table with the filename in a new field
    """
    
    import os
    from gasp.pyt.oss    import lst_ff
    from gasp.gt.tbl.fld import add_fields
    
    if os.path.isdir(tables):
        __tables = lst_ff(tables, file_format=table_format)
    
    else:
        __tables = [tables]
    
    for table in __tables:
        add_fields(table, {new_field: 'varchar(50)'})
        
        name_tbl = os.path.splitext(os.path.basename(table))[0]
        name_tbl = name_tbl.lower() if name_tbl.isupper() else name_tbl
        update_cols(
            table, {new_field: name_tbl}
        )

