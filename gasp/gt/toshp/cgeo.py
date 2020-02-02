"""
Geometry conversion/change operations
"""

def feat_vertex_to_pnt(inShp, outPnt, nodes=True):
    """
    Feature Class to a Point Feature Class
    
    v.to.points - Creates points along input lines in new vector map with
    2 layers.
    
    v.to.points creates points along input 2D or 3D lines, boundaries and
    faces. Point features including centroids and kernels are copied from
    input vector map to the output. For details see notes about type parameter.
    
    The output is a vector map with 2 layers. Layer 1 holds the category of
    the input features; all points created along the same line have the same
    category, equal to the category of that line. In layer 2 each point has
    its unique category; other attributes stored in layer 2 are lcat - the
    category of the input line and along - the distance from line's start.
    
    By default only features with category are processed, see layer parameter
    for details.
    """
    
    from grass.pygrass.modules import Module
    
    toPnt = Module(
        "v.to.points", input=inShp,
        output=outPnt,
        use="node" if nodes else "vertex",
        overwrite=True, run_=False,
        quiet=True
    )
    
    toPnt()
    
    return outPnt
