"""
OSM2LULC using Numpy
"""


def osm2lulc(osmdata, nomenclature, refRaster, lulcRst,
             overwrite=None, dataStore=None, roadsAPI='POSTGIS'):
    """
    Convert OSM data into Land Use/Land Cover Information
    
    A matrix based approach
    
    roadsAPI Options:
    * SQLITE
    * POSTGIS
    """
    
    # ************************************************************************ #
    # Python Modules from Reference Packages #
    # ************************************************************************ #
    import os; import numpy; import datetime; import json
    from threading import Thread
    from osgeo     import gdal
    # ************************************************************************ #
    # Dependencies #
    # ************************************************************************ #
    from gasp3.dt.fm.rst              import rst_to_array
    from gasp3.gt.prop.ff             import check_isRaster
    from gasp3.gt.prop.rst            import get_cellsize
    from gasp3.gt.prop.prj            import get_rst_epsg
    from gasp3.pyt.oss                import create_folder, copy_file
    if roadsAPI == 'POSTGIS':
        from gasp3.sql.mng.db         import create_db
        from gasp3.alg.osm2lulc.utils import osm_to_pgsql
        from gasp3.alg.osm2lulc.mod2  import pg_num_roads
    else:
        from gasp3.alg.osm2lulc.utils import osm_to_sqdb
        from gasp3.alg.osm2lulc.mod2  import num_roads
    from gasp3.alg.osm2lulc.utils     import osm_project, add_lulc_to_osmfeat
    from gasp3.alg.osm2lulc.utils     import osmlulc_rsttbl
    from gasp3.alg.osm2lulc.utils     import get_ref_raster
    from gasp3.alg.osm2lulc.mod1      import num_selection
    from gasp3.alg.osm2lulc.m3_4      import num_selbyarea
    from gasp3.alg.osm2lulc.mod5      import num_base_buffer
    from gasp3.alg.osm2lulc.mod6      import num_assign_builds
    from gasp3.dt.to.rst              import array_to_raster
    # ************************************************************************ #
    # Global Settings #
    # ************************************************************************ #
    # Check if input parameters exists!
    if not os.path.exists(os.path.dirname(lulcRst)):
        raise ValueError('{} does not exist!'.format(os.path.dirname(lulcRst)))
    
    if not os.path.exists(osmdata):
        raise ValueError('File with OSM DATA ({}) does not exist!'.format(osmdata))
    
    if not os.path.exists(refRaster):
        raise ValueError('File with reference area ({}) does not exist!'.format(refRaster))
    
    # Check if Nomenclature is valid
    nomenclature = "URBAN_ATLAS" if nomenclature != "URBAN_ATLAS" and \
        nomenclature != "CORINE_LAND_COVER" and \
        nomenclature == "GLOBE_LAND_30" else nomenclature
    
    time_a = datetime.datetime.now().replace(microsecond=0)
    
    workspace = os.path.join(os.path.dirname(
        lulcRst), 'num_osmto') if not dataStore else dataStore
    
    # Check if workspace exists:
    if os.path.exists(workspace):
        if overwrite:
            create_folder(workspace, overwrite=True)
        else:
            raise ValueError('Path {} already exists'.format(workspace))
    else:
        create_folder(workspace, overwrite=None)
    
    conPGSQL = json.load(open(os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'con-postgresql.json'
    ), 'r')) if roadsAPI == 'POSTGIS' else None
    
    # Get Ref Raster and EPSG
    refRaster, epsg = get_ref_raster(refRaster, workspace, cellsize=2)
    CELLSIZE = get_cellsize(refRaster, gisApi='gdal')
        
    from gasp3.alg.osm2lulc.var import osmTableData, PRIORITIES
    
    time_b = datetime.datetime.now().replace(microsecond=0)
    # ************************************************************************ #
    # Convert OSM file to SQLITE DB or to POSTGIS DB #
    # ************************************************************************ #
    if roadsAPI == 'POSTGIS':
        conPGSQL["DATABASE"] = create_db(conPGSQL, os.path.splitext(
            os.path.basename(osmdata))[0], overwrite=True)
        osm_db = osm_to_pgsql(osmdata, conPGSQL)
    
    else:
        osm_db = osm_to_sqdb(osmdata, os.path.join(workspace, 'osm.sqlite'))
    time_c = datetime.datetime.now().replace(microsecond=0)
    # ************************************************************************ #
    # Add Lulc Classes to OSM_FEATURES by rule #
    # ************************************************************************ #
    add_lulc_to_osmfeat(
        conPGSQL if roadsAPI=='POSTGIS' else osm_db,
        osmTableData, nomenclature, api=roadsAPI
    )
    time_d = datetime.datetime.now().replace(microsecond=0)
    # ************************************************************************ #
    # Transform SRS of OSM Data #
    # ************************************************************************ #
    osmTableData = osm_project(
        conPGSQL if roadsAPI == 'POSTGIS' else osm_db, epsg, api=roadsAPI,
        isGlobeLand=None if nomenclature != "GLOBE_LAND_30" else True
    )
    time_e = datetime.datetime.now().replace(microsecond=0)
    # ************************************************************************ #
    # MapResults #
    # ************************************************************************ #
    mergeOut  = {}
    timeCheck = {}
    RULES = [1, 2, 3, 4, 5, 7]
    
    def run_rule(ruleID):
        time_start = datetime.datetime.now().replace(microsecond=0)
        _osmdb = copy_file(
            osm_db, os.path.splitext(osm_db)[0] + '_r{}.sqlite'.format(ruleID)
        ) if roadsAPI == 'SQLITE' else None
        # ******************************************************************** #
        # 1 - Selection Rule #
        # ******************************************************************** #
        if ruleID == 1:
            res, tm = num_selection(
                conPGSQL if not _osmdb else _osmdb,
                osmTableData['polygons'], workspace, CELLSIZE, epsg, refRaster,
                api=roadsAPI
            )
        # ******************************************************************** #
        # 2 - Get Information About Roads Location #
        # ******************************************************************** #
        elif ruleID == 2:
            res, tm = num_roads(
                _osmdb, nomenclature, osmTableData['lines'],
                osmTableData['polygons'], workspace, CELLSIZE, epsg,
                refRaster
            ) if _osmdb else pg_num_roads(
                conPGSQL, nomenclature,
                osmTableData['lines'], osmTableData['polygons'],
                workspace, CELLSIZE, epsg, refRaster
            )
        
        # ******************************************************************** #
        # 3 - Area Upper than #
        # ******************************************************************** #
        elif ruleID == 3:
            if nomenclature != "GLOBE_LAND_30":
                res, tm = num_selbyarea(
                    conPGSQL if not _osmdb else _osmdb,
                    osmTableData['polygons'], workspace,
                    CELLSIZE, epsg, refRaster, UPPER=True, api=roadsAPI
                )
            else:
                return
        
        # ******************************************************************** #
        # 4 - Area Lower than #
        # ******************************************************************** #
        elif ruleID == 4:
            if nomenclature != "GLOBE_LAND_30":
                res, tm = num_selbyarea(
                    conPGSQL if not _osmdb else _osmdb,
                    osmTableData['polygons'], workspace,
                    CELLSIZE, epsg, refRaster, UPPER=False, api=roadsAPI
                )
            else:
                return
        
        # ******************************************************************** #
        # 5 - Get data from lines table (railway | waterway) #
        # ******************************************************************** #
        elif ruleID == 5:
            res, tm = num_base_buffer(
                conPGSQL if not _osmdb else _osmdb,
                osmTableData['lines'], workspace,
                CELLSIZE, epsg, refRaster, api=roadsAPI
            )
        # ******************************************************************** #
        # 7 - Assign untagged Buildings to tags #
        # ******************************************************************** #
        elif ruleID == 7:
            if nomenclature != "GLOBE_LAND_30":
                res, tm = num_assign_builds(
                    conPGSQL if not _osmdb else _osmdb,
                    osmTableData['points'], osmTableData['polygons'],
                    workspace, CELLSIZE, epsg, refRaster, apidb=roadsAPI
                )
            
            else:
                return
        
        time_end = datetime.datetime.now().replace(microsecond=0)
        mergeOut[ruleID] = res
        timeCheck[ruleID] = {'total': time_end - time_start, 'detailed': tm}
    
    thrds = []
    for r in RULES:
        thrds.append(Thread(
            name="to_{}".format(str(r)), target=run_rule,
            args=(r,)
        ))
        
    
    for t in thrds: t.start()
    for t in thrds: t.join()
    
    # Merge all results into one Raster
    compileResults = {}
    for rule in mergeOut:
        for cls in mergeOut[rule]:
            if cls not in compileResults:
                if type(mergeOut[rule][cls]) == list:
                    compileResults[cls] = mergeOut[rule][cls]
                else:
                    compileResults[cls] = [mergeOut[rule][cls]]
            
            else:
                if type(mergeOut[rule][cls]) == list:
                    compileResults[cls] += mergeOut[rule][cls]
                else:
                    compileResults[cls].append(mergeOut[rule][cls])
    
    time_m = datetime.datetime.now().replace(microsecond=0)
    # All Rasters to Array
    arrayRst = {}
    for cls in compileResults:
        for raster in compileResults[cls]:
            if not raster:
                continue
            
            array = rst_to_array(raster)
            
            if cls not in arrayRst:
                arrayRst[cls] = [array.astype(numpy.uint8)]
            
            else:
                arrayRst[cls].append(array.astype(numpy.uint8))
    time_n = datetime.datetime.now().replace(microsecond=0)
    
    # Sum Rasters of each class
    for cls in arrayRst:
        if len(arrayRst[cls]) == 1:
            sumArray = arrayRst[cls][0]
        
        else:
            sumArray = arrayRst[cls][0]
            
            for i in range(1, len(arrayRst[cls])):
                sumArray = sumArray + arrayRst[cls][i]
        
        arrayRst[cls] = sumArray
    
    time_o = datetime.datetime.now().replace(microsecond=0)
    
    # Apply priority rule
    __priorities = PRIORITIES[nomenclature + "_NUMPY"]
    
    for lulcCls in __priorities:
        __lulcCls = 1222 if lulcCls == 98 else 1221 if lulcCls == 99 else \
            802 if lulcCls == 82 else 801 if lulcCls == 81 else lulcCls
        if __lulcCls not in arrayRst:
            continue
        else:
            numpy.place(arrayRst[__lulcCls], arrayRst[__lulcCls] > 0,
                lulcCls
            )
    
    for i in range(len(__priorities)):
        lulc_i = 1222 if __priorities[i] == 98 else 1221 \
            if __priorities[i] == 99 else 802 if __priorities[i] == 82 \
            else 801 if __priorities[i] == 81 else __priorities[i]
        if lulc_i not in arrayRst:
            continue
        
        else:
            for e in range(i+1, len(__priorities)):
                lulc_e = 1222 if __priorities[e] == 98 else 1221 \
                    if __priorities[e] == 99 else \
                    802 if __priorities[e] == 82 else 801 \
                    if __priorities[e] == 81 else __priorities[e]
                if lulc_e not in arrayRst:
                    continue
                
                else:
                    numpy.place(arrayRst[lulc_e],
                        arrayRst[lulc_i] == __priorities[i], 0
                    )
    
    time_p = datetime.datetime.now().replace(microsecond=0)
    
    # Merge all rasters
    startCls = 'None'
    for i in range(len(__priorities)):
        lulc_i = 1222 if __priorities[i] == 98 else 1221 \
            if __priorities[i] == 99 else 802 if __priorities[i] == 82 \
            else 801 if __priorities[i] == 81 else __priorities[i]
        if lulc_i in arrayRst:
            resultSum = arrayRst[lulc_i]
            startCls = i
            break
    
    if startCls == 'None':
        return 'NoResults'
    
    for i in range(startCls + 1, len(__priorities)):
        lulc_i = 1222 if __priorities[i] == 98 else 1221 \
            if __priorities[i] == 99 else 802 if __priorities[i] == 82 \
            else 801 if __priorities[i] == 81 else __priorities[i]
        if lulc_i not in arrayRst:
            continue
        
        resultSum = resultSum + arrayRst[lulc_i]
    
    # Save Result
    outIsRst = check_isRaster(lulcRst)
    if not outIsRst:
        from gasp3.pyt.oss import get_filename
        
        lulcRst = os.path.join(
            os.path.dirname(lulcRst), get_filename(lulcRst) + '.tif'
        )
    
    numpy.place(resultSum, resultSum==0, 1)
    array_to_raster(
        resultSum, lulcRst, refRaster, noData=1
    )
    
    osmlulc_rsttbl(nomenclature + "_NUMPY", os.path.join(
        os.path.dirname(lulcRst), os.path.basename(lulcRst) + '.vat.dbf'
    ))
    
    time_q = datetime.datetime.now().replace(microsecond=0)
    
    return lulcRst, {
        0  : ('set_settings', time_b - time_a),
        1  : ('osm_to_sqdb', time_c - time_b),
        2  : ('cls_in_sqdb', time_d - time_c),
        3  : ('proj_data', time_e - time_d),
        4  : ('rule_1', timeCheck[1]['total'], timeCheck[1]['detailed']),
        5  : ('rule_2', timeCheck[2]['total'], timeCheck[2]['detailed']),
        6  : None if 3 not in timeCheck else (
            'rule_3', timeCheck[3]['total'], timeCheck[3]['detailed']),
        7  : None if 4 not in timeCheck else (
            'rule_4', timeCheck[4]['total'], timeCheck[4]['detailed']),
        8  : ('rule_5', timeCheck[5]['total'], timeCheck[5]['detailed']),
        9  : None if 7 not in timeCheck else (
            'rule_7', timeCheck[7]['total'], timeCheck[7]['detailed']),
        10 : ('rst_to_array', time_n - time_m),
        11 : ('sum_cls', time_o - time_n),
        12 : ('priority_rule', time_p - time_o),
        13 : ('merge_rst', time_q - time_p)
    }
