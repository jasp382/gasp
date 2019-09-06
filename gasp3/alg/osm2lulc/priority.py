"""
Priority rule implementation
"""


def priority_rule(osmshps, priorities, gis_software, param=None):
    """
    Priority rule in Arcgis
    """
    
    import copy; import os
    if gis_software != 'psql':
        from gasp3.gt.anls.ovlay import erase
    else:
        from gasp3.sql.anls.ovlay import pg_erase
    from gasp3.pyt.oss import get_filename
    
    osmNameRef = copy.deepcopy(osmshps)
    
    for e in range(len(priorities)):
        if e + 1 == len(priorities): break
        
        if priorities[e] not in osmshps:
            continue
        
        else:
            for i in range(e+1, len(priorities)):
                if priorities[i] not in osmshps:
                    continue
                
                else:
                    if gis_software == 'arcpy':
                        tmpOut = os.path.join(
                            os.path.dirname(osmshps[priorities[i]]),
                            "{}_{}.shp".format(
                                get_filename(osmNameRef[priorities[i]]), e
                            )
                        )
                    
                    else:
                        tmpOut = "{}_{}".format(osmNameRef[priorities[i]], e)
                    
                    if gis_software == 'psql':
                        osmshps[priorities[i]] = pg_erase(
                            param, osmshps[priorities[i]],
                            osmshps[priorities[e]], 'geom', 'geom',
                            tmpOut
                        )
                    
                    else:  
                        osmshps[priorities[i]] = erase(
                            osmshps[priorities[i]], osmshps[priorities[e]],
                            tmpOut, api=gis_software
                        )
    
    return osmshps

