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

