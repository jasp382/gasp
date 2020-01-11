"""
Reclassify Raster files
"""

def rcls_rst(inrst, rclsRules, outrst, api='gdal'):
    """
    Reclassify a raster (categorical and floating points)
    
    if api == 'gdal
    rclsRules = {
        1 : 99,
        2 : 100
        ...
    }
    
    or
    
    rclsRules = {
        (0, 8) : 1
        (8, 16) : 2
        '*'       : 'NoData'
    }
    
    elif api == grass:
    rclsRules should be a path to a text file
    """
    
    if api == 'gdal':
        import numpy          as np
        from osgeo            import gdal
        from gasp.gt.to.rst   import obj_to_rst
        from gasp.g.fm        import imgsrc_to_num
        from gasp.g.prop.img import get_nd

        # Open Raster
        img = gdal.Open(inrst)
    
        # Raster to Array
        rst_num = imgsrc_to_num(img)
    
        nodataVal = get_nd(img)
    
        rcls_num = np.zeros(rst_num.shape, rst_num.dtype)
    
        # Change values
        for k in rclsRules:
            if type(k) == tuple:
                np.place(
                    rcls_num, (rst_num > k[0]) & (rst_num <= k[1]),
                    rclsRules[k] if rclsRules != 'NoData' else nodataVal
                )
            elif type(k) == str:
                continue
            else:
                np.place(rcls_num, rst_num == k, rclsRules[k])
    
        if '*' in rclsRules:
            np.place(
                rcls_num, rcls_num == 0,
                nodataVal if rclsRules['*'] == 'NoData' else rclsRules['*']
            )
        else:
            np.place(rcls_num, rcls_num == 0, nodataVal)
    
        if 'NoData' in rclsRules:
            np.place(rcls_num, rst_num == nodataVal, rclsRules['NoData'])
        else:
            np.place(rcls_num, rst_num == nodataVal, nodataVal)
    
        return obj_to_rst(rcls_num, outrst, img, noData=nodataVal)
    
    elif api == "pygrass":
        from grass.pygrass.modules import Module
        
        r = Module(
            'r.reclass', input=inrst, output=outrst, rules=rclsRules,
            overwrite=True, run_=False, quiet=True
        )
        
        r()
    
    else:
        raise ValueError((
            "API {} is not available"
        ).format(api))


"""
Reclassify in GRASS GIS
"""


def interval_rules(dic, out_rules):
    """
    Write rules file for reclassify - in this method, intervals will be 
    converted in new values
    
    dic = {
        new_value1: {'base': x, 'top': y},
        new_value2: {'base': x, 'top': y},
        ...,
        new_valuen: {'base': x, 'top': y}
    }
    """
    
    import os
    
    if os.path.splitext(out_rules)[1] != '.txt':
        out_rules = os.path.splitext(out_rules)[0] + '.txt'
    
    with open(out_rules, 'w') as txt:
        for new_value in dic:
            txt.write(
                '{b} thru {t}  = {new}\n'.format(
                    b=str(dic[new_value]['base']),
                    t=str(dic[new_value]['top']),
                    new=str(new_value)
                )
            )
        txt.close()
    
    return out_rules


def category_rules(dic, out_rules):
    """
    Write rules file for reclassify - in this method, categorical values will be
    converted into new designations/values
    
    dic = {
        new_value : old_value,
        new_value : old_value,
        ...
    }
    """
    
    if os.path.splitext(out_rules)[1] != '.txt':
        out_rules = os.path.splitext(out_rules)[0] + '.txt'
    
    with open(out_rules, 'w') as txt:
        for k in dic:
            txt.write(
                '{n}  = {o}\n'.format(o=str(dic[k]), n=str(k))
            )
        
        txt.close()
    
    return out_rules


def set_null(rst, value, ascmd=None):
    """
    Null in Raster to Some value
    """
    
    if not ascmd:
        from grass.pygrass.modules import Module
        
        m = Module(
            'r.null', map=rst, setnull=value, run_=False, quiet=True
        )
        
        m()
    
    else:
        from gasp import exec_cmd
        
        rcmd = exec_cmd("r.null map={} setnull={} --quiet".format(
            rst, value
        ))


def null_to_value(rst, value, as_cmd=None):
    """
    Give a numeric value to the NULL cells
    """
    
    if not as_cmd:
        from grass.pygrass.modules import Module
        
        m = Module(
            'r.null', map=rst, null=value, run_=False, quiet=True
        )
        m()
    
    else:
        from gasp import exec_cmd
        
        rcmd = exec_cmd("r.null map={} null={} --quiet".format(
            rst, value
        ))

