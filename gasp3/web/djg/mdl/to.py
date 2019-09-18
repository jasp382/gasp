"""
Data to Django Model
"""

def shp_to_djg_mdl(fileShape, djgModel, mapFields, djgProj=None, useLyrMap=True):
    """
    Add Geometries to Django Model
    """
    
    from gasp3 import __import
    
    if djgProj:
        from gasp3.web.djg import open_Django_Proj
        
        application = open_Django_Proj(djgProj)
    
    APP_MODEL = djgModel.split('_')[0]
    djangoCls = __import('{}.models.{}'.format(
        APP_MODEL,
        '_'.join(djgModel.split('_')[1:])
    ))
    
    if useLyrMap:
        from django.contrib.gis.utils import LayerMapping
        
        lm = LayerMapping(djangoCls, fileShape, mapFields)
        
        lm.save(strict=True, verbose=False)
    
    else:
        from django.contrib.gis.geos import GEOSGeometry
        from django.contrib.gis.db   import models
        from gasp3.fm                import tbl_to_obj
        
        inDf = tbl_to_obj(inShp)
        
        modelObj = djangoCls()
        
        OGR_GEOMS = ['POLYGON', 'MULTIPOLYGON', 'MULTILINESTRING',
                     'LINESTRING', 'POINT', 'MULTIPOINT']
        
        def updateModel(row):
            for FLD in mapFields:
                if mapFields[FLD] not in OGR_GEOMS:
                    # Check if field is foreign key
                    field_obj = djangoCls._meta.get_field(FLD)
                
                    if not isinstance(field_obj, models.ForeignKey):
                        setattr(modelObj, FLD, row[mapFields[FLD]])
                
                    else:
                        # If yes, use the model instance of the related table
                        # Get model of the table related com aquela cujos dados
                        # estao a ser restaurados
                        related_name = field_obj.related_model.__name__
                    
                        related_model = __import('{a}.models.{m}'.format(
                            a=APP_MODEL[0], m=related_name
                        ))
                    
                        related_obj = related_model.objects.get(
                            pk=int(row[mapFields[FLD]])
                        )
                    
                        setattr(modelObj, FLD, related_obj)
            
                else:
                    setattr(modelObj, FLD, GEOSGeometry(
                        row.geometry.wkt, srid=epsg
                    ))
        
            modelObj.save()
        
        inDf.apply(lambda x: updateModel(x), axis=1)


def txt_to_db(txt, proj_path=None, delimiter='\t', encoding_='utf-8'):
    """
    Read a txt with table data and import it to the database using
    django API.
    
    Use the filename of the text file to identify the correspondent django
    model.
    
    Proj_path is not necessary if you are running this method in Django shell
    
    IMPORTANT NOTE:
    This method will work only if all foreign key columns have the same name
    of their models.
    """
    
    import codecs;           import os
    from gasp3               import __import
    from gasp3.web.djg.mdl.i import get_special_tables
    
    def sanitize_value(v):
        _v = None if v=='None' or v =='' else v
        
        if not _v:
            return _v
        else:
            try:
                __v = float(_v)
                if __v == int(__v):
                    return int(__v)
                else:
                    return __v
            except:
                return _v
    
    if not os.path.exists(txt) and not os.path.isfile(txt):
        raise ValueError('Path given is not valid')
    
    # Open Django Project
    if proj_path:
        from gasp3.web.djg import open_Django_Proj
        
        application = open_Django_Proj(proj_path)
    
    from django.contrib.gis.db import models
    
    table_name = os.path.splitext(os.path.basename(txt))[0]
    
    SPECIAL_TABLES = get_special_tables()
    
    if table_name in SPECIAL_TABLES:
        str_to_import_cls = SPECIAL_TABLES[table_name]
        
    else:
        djg_app = table_name.split('_')[0]
        
        djg_model_name = '_'.join(table_name.split('_')[1:])
        
        str_to_import_cls = '{a}.models.{t}'.format(
            a=djg_app, t=djg_model_name
        )
    
    djangoCls = __import(str_to_import_cls)
    
    # Map data in txt
    with codecs.open(txt, 'r', encoding=encoding_) as f:
        c = 0
        data = []
        
        for l in f:
            cols = l.replace('\r', '').strip('\n').split(delimiter)
            
            if not c:
                cols_name = ['%s' % cl for cl in cols]
                c += 1
            else:
                data.append([sanitize_value(v) for v in cols])
        
        f.close()
    
    # Import data to django class and db
    __model = djangoCls()
    for row in data:
        for c in range(len(row)):
            # Check if field is a foreign key
            field_obj = djangoCls._meta.get_field(cols_name[c])
            if not isinstance(field_obj, models.ForeignKey):
                # If not, use the value
                setattr(__model, cols_name[c], row[c])
            else:
                # If yes, use the model instance of the related table
                # Get model of the table related com aquela cujos dados 
                # estao a ser restaurados
                related_name = field_obj.related_model.__name__
                related_model = __import('{a}.models.{m}'.format(
                    a=djg_app, m=related_name
                ))
                related_obj = related_model.objects.get(pk=int(row[c]))
                setattr(__model, cols_name[c], related_obj)
        __model.save()


def txts_to_db(folder, delimiter='\t', _encoding_='utf-8', proj_path=None):
    """
    List all txt files in a folder and import their data to the 
    database using django API.
    
    The txt files name must be equal to the name of the
    correspondent table.
    
    Proj_path is not necessary if you are running this method in Django shell
    """
    
    import os, sys
    from gasp3                 import __import
    from gasp3.pyt.oss         import lst_ff
    from gasp3.web.djg.mdl.rel import order_models_by_relation
    
    # Open Django Project
    if proj_path:
        from gasp3.web.djg import open_Django_Proj
        application = open_Django_Proj(proj_path)
    
    # List txt files
    if not os.path.exists(folder) and not os.path.isdir(folder):
        raise ValueError('Path given is not valid!')
    
    # Get importing order
    txt_tables = [
        os.path.splitext(os.path.basename(x))[0] for x in lst_ff(
            folder, file_format='.txt'
        )
    ]
    
    orderned_table = order_models_by_relation(txt_tables)
    
    for table in orderned_table:
        if table in txt_tables:
            print('Importing {}'.format(table))
            txt_to_db(
                os.path.join(folder, table + '.txt'),
                delimiter=delimiter,
                encoding_=_encoding_
            )
            print('{} is in the database'.format(table))
        else:
            print('Skipping {} - there is no file for this table'.format(table))


def psql_to_djgdb(sql_file, tmp_db_name, path_djgProj=None, psql_con={
    'HOST': 'localhost', 'USER': 'postgres',
    'PORT' : '5432', 'PASSWORD': 'admin',
    'TEMPLATE': 'postgis_template'}, mapTbl=None):
    """
    Import PGSQL database in a SQL Script into the database
    controlled by one Django Project
    
    To work, the name of a model instance of type foreign key should be
    equal to the name of the 'db_column' clause.
    """
    
    import os
    from gasp3                 import __import
    from gasp3.sql             import run_sql_script
    from gasp3.sql.mng.db      import create_db
    from gasp3.sql.i           import lst_tbl
    from gasp3.sql.fm          import tbl_to_dict
    from gasp3.web.djg.mdl.i   import get_special_tables
    from gasp3.web.djg.mdl.rel import order_models_by_relation
    
    TABLES_TO_EXCLUDE = [
        'geography_columns', 'geometry_columns',
        'spatial_ref_sys', 'raster_columns', 'raster_columns',
        'raster_overviews', 'pointcloud_formats', 'pointcloud_columns'
    ]
    
    SPECIAL_TABLES = get_special_tables()
    
    # Import SQL to a new database
    create_db(psql_con, tmp_db_name)
    
    run_sql_script(psql_con, tmp_db_name, sql_file)
    
    psql_con["DATABASE"] = tmp_db_name
    # List tables in the database
    tables = {x : x for x in lst_tbl(
        psql_con, excludeViews=True, api='psql')} if not mapTbl else mapTbl
    
    # Open Django Project
    if path_djgProj:
        from gasp3.web.djg import open_Django_Proj
        application = open_Django_Proj(path_djgProj)
    
    # List models in project
    from gasp3.web.djg.mdl.i import lst_mdl_proj
    appModels = lst_mdl_proj(path_djgProj, thereIsApp=True)
    
    data_tables = {}
    for table in tables:
        if tables[table].startswith('auth') or tables[table].startswith('django') \
           or tables[table] in TABLES_TO_EXCLUDE:
            if tables[table] == 'auth_user':
                data_tables[table] = tables[table]
            else:
                continue
        
        elif tables[table] not in appModels:
            continue
        
        else:
            data_tables[table] = tables[table]
    
    __tbls = {data_tables[t] : t for t in data_tables}
    
    from django.contrib.gis.db import models
    orderned_table = order_models_by_relation(__tbls.keys())
    
    for table in orderned_table:
        # Map pgsql table data
        # TODO: table could not be in the restore db
        tableData = tbl_to_dict(__tbls[table], psql_con)
        
        # Table data to Django Model
        if table in SPECIAL_TABLES:
            djangoCls = __import(SPECIAL_TABLES[table])
        else:
            djg_app = table.split('_')[0]
            djg_model_name = '_'.join(table.split('_')[1:])
        
            djangoCls = __import('{a}.models.{t}'.format(
                a=djg_app, t=djg_model_name
            ))
        
        __model = djangoCls()
        
        for row in tableData:
            for col in row:
                # Check if field is a foreign key
                field_obj = djangoCls._meta.get_field(col)
                
                if not isinstance(field_obj, models.ForeignKey):
                    # If not, use the value
                    
                    # But first check if value is nan (special type of float)
                    if row[col] != row[col]:
                        row[col] = None
                        
                    setattr(__model, col, row[col])
                
                else:
                    # If yes, use the model instance of the related table
                    # Get model of the table related com aquela cujos dados 
                    # estao a ser restaurados
                    related_name = field_obj.related_model.__name__
                    related_model = __import('{a}.models.{m}'.format(
                        a=djg_app, m=related_name
                    ))
                    
                    # If NULL, continue
                    if not row[col]:
                        setattr(__model, col, row[col])
                        continue
                    
                    related_obj = related_model.objects.get(
                        pk=int(row[col])
                    )
                    
                    setattr(__model, col, related_obj)
            __model.save()

