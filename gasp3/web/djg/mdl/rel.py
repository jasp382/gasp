"""
Get relations between django models
"""

from gasp3 import __import


def order_models_by_relation(tables):
    """
    Receive a group of tables and see which tables should be
    imported first in the database. Tables depending on others should be
    imported after them.
    """
    
    import os
    from gasp3.web.djg.mdl.i   import list_tables_without_foreignk
    from gasp3.web.djg.mdl.i   import get_special_tables, get_ignore_tables
    from django.contrib.gis.db import models
    
    SPECIAL_MODELS = get_special_tables()
    IGNORE_TABLES = get_ignore_tables()
    
    def get_childs(treeObj):
        for table in treeObj:
            # Get model object
            if table not in SPECIAL_MODELS:
                app = table.split('_')[0]
                modObj = __import('{}.models.{}'.format(
                    app, '_'.join(table.split('_')[1:])
                ))
            else:
                modObj = __import(SPECIAL_MODELS[table])
            
            rel_model_name = None
            rel_app_name = None
        
            fields = modObj._meta.get_fields()
        
            for field in fields:
                if not isinstance(field, models.ForeignKey):
                    if hasattr(field, 'related_model'):
                        if hasattr(field.related_model, '__name__'):
                            rel_model_name = field.related_model.__name__
                            rel_app_name   = field.related_model.__module__.split('.')[0]
                        else:
                            rel_model_name = None
                            rel_app_name = None
                    else:
                        rel_model_name = None
                        rel_app_name = None
                else:
                    rel_model_name = None
                    rel_app_name = None
        
                if rel_model_name and rel_app_name:
                    rmn = '{}_{}'.format(rel_app_name, rel_model_name)
                    
                    if rmn in IGNORE_TABLES:
                        continue
                    
                    treeObj[table].update({rmn: {}})
        
                else: 
                    continue
            
            if treeObj[table]:
                get_childs(treeObj[table])
            else: continue
    
    
    def get_table_level(nodes, level, dic):
        for node in nodes:
            if level not in dic:
                dic[level] = [node]
            else:
                dic[level].append(node)
            
            if not nodes[node]:
                continue
            else:
                get_table_level(nodes[node], level + 1, dic)
    
    # Get root
    root_tables = list_tables_without_foreignk(tables)
    tree = {
        os.path.splitext(os.path.basename(
            root))[0] : {} for root in root_tables
    }
    
    get_childs(tree)
    
    tables_by_level = {}
    get_table_level(tree, 0, tables_by_level)
    
    # Levels to a single list
    ordened = []
    for i in range(len(tables_by_level.keys())):
        for table in tables_by_level[i]:
            ordened.append(table)
    
    clean = []
    for i in range(len(ordened)):
        if i+1 != len(ordened):
            if ordened[i] not in ordened[i+1:]:
                clean.append(ordened[i])
            else: continue
        else:
            if ordened[i] not in clean:
                clean.append(ordened[i])
    
    return clean

