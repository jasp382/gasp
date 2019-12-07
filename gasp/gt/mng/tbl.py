"""
Using Tables
"""


"""
Record Geometric Properties in some Table
"""

def geomattr_to_db(shp, attrCol, attr, geomType, createCol=True,
                   unit=None, lyrN=1, ascmd=None):
    """
    v.to.db - Populates attribute values from vector features.
    
    v.to.db loads vector map features or metrics into a database table,
    or prints them (or the SQL queries used to obtain them) in a form
    of a human-readable report. For uploaded/printed category values '-1'
    is used for 'no category' and 'null'/'-' if category cannot be
    found or multiple categories were found. For line azimuths '-1' is used
    for closed lines (start equals end).
    
    attrs options area:
    * cat: insert new row for each category if doesn't exist yet
    * area: area size
    * compact: compactness of an area, calculated as 
    compactness = perimeter / (2 * sqrt(PI * area))
    * fd: fractal dimension of boundary defining a polygon, calculated as
    fd = 2 * (log(perimeter) / log(area))
    * perimeter: perimeter length of an area
    * length: line length
    * count: number of features for each category
    * coor: point coordinates, X,Y or X,Y,Z
    * start: line/boundary starting point coordinates, X,Y or X,Y,Z
    * end: line/boundary end point coordinates, X,Y or X,Y,Z
    * sides: categories of areas on the left and right side of the boundary,
    'query_layer' is used for area category
    * query: result of a database query for all records of the geometry(or
    geometries) from table specified by 'query_layer' option
    * slope: slope steepness of vector line or boundary
    * sinuous: line sinuousity, calculated as line length / distance between
    end points
    * azimuth: line azimuth, calculated as angle between North direction and
    endnode direction at startnode
    * bbox: bounding box of area, N,S,E,W
    """
    
    from gasp.pyt import obj_to_lst
    
    attrCol = obj_to_lst(attrCol)
    
    if createCol:
        from gasp.gt.tbl.fld import add_fields
        
        for c in attrCol:
            add_fields(
                shp, {c : "DOUBLE PRECISION"},
                api="grass" if ascmd else "pygrass"
            ) 
    
    if not ascmd:
        from grass.pygrass.modules import Module
        
        vtodb = Module(
            "v.to.db", map=shp, type=geomType, layer=lyrN, option=attr,
            columns=",".join(attrCol) if attr != 'length' else attrCol[0],
            units=unit, run_=False, quiet=True
        )
        
        vtodb()
    
    else:
        from gasp import exec_cmd
        
        rcmd = exec_cmd((
            "v.to.db map={} type={} layer={} option={} "
            "columns={} units={} --quiet"
        ).format(
            shp, geomType, lyrN, attr,
            ",".join(attrCol) if attr != 'length' else attrCol[0],
            unit
        ))


def add_geomattr_to_sqldbTbl(sqdb, table, geom_attr, newTblName, newColName):
    """
    Use ogr2ogr to add geometry attributes to table
    """
    
    from gasp import exec_cmd
    
    cmd = (
        "ogr2ogr -update -append -f \"SQLite\" {db} -nln \"{nt}\" "
        "-dialect sqlite -sql \"SELECT *, {geomProp}(geometry) "
        "AS {newCol} FROM {tbl}\" {db}"
    ).format(
        db=sqdb, nt=newTblName, geomProp=geom_attr,
        newCol=newColName, tbl=table
    )
    
    rcmd = exec_cmd(cmd)
    
    return newTblName

"""
Copy Features
"""

def copy_insame_vector(inShp, colToBePopulated, srcColumn, destinyLayer,
                       geomType="point,line,boundary,centroid",
                       asCMD=None):
    """
    Copy Field values from one layer to another in the same GRASS Vector
    """
    
    if not asCMD:
        from grass.pygrass.modules import Module
        
        vtodb = Module(
            "v.to.db", map=inShp, layer=destinyLayer, type=geomType,
            option="query", columns=colToBePopulated,
            query_column=srcColumn, run_=False, quiet=True
        )
    
        vtodb()
    
    else:
        from gasp import exec_cmd
        
        rcmd = exec_cmd((
            "v.to.db map={} layer={} type={} option=query columns={} "
            "query_column={} --quiet"
        ).format(inShp, destinyLayer, geomType, colToBePopulated,
                 srcColumn))


"""
Summarizing
"""

def summarize_table_fields(table, outFld, fld_name_fld_name=None,
                          __upper=False):
    """
    Summarize all fields in a table
    """
    
    import os
    from gasp         import exec_cmd
    from gasp.pyt.oss import mkdir
    
    # List table fields:
    fields = lst_fld(table)
    
    # For each field, query data to summarize the values in the field
    cmd = 'ogr2ogr {o} {i} -dialect sqlite -sql "{s};"'
    
    if not os.path.exists(outFld):
        tmp = mkdir(outFld)
    
    for field in fields:
        outTbl = os.path.join(outFld, '{}.dbf'.format(field))
        
        outcmd = exec_cmd(cmd.format(
            i=table, o=outTbl,
            s='SELECT {f_}{f} FROM {t} GROUP BY {f}'.format(
                f=field,
                t=os.path.splitext(os.path.basename(table))[0],
                f_='' if not fld_name_fld_name else '{}, '.format(
                    fld_name_fld_name
                )
            )
        ))

