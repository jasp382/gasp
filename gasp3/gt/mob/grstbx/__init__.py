"""
GIS API's subpackage:

GRASS GIS Python tools for network analysis
"""


"""
Create and Mantain network
"""
def network_from_arcs(networkFC, networkOUT):
    """
    v.net is used for network preparation and maintenance. Its main use is
    to create a vector network from vector lines (arcs ) and points (nodes)
    by creating nodes from intersections in a map of vector lines
    (node operator), by connecting a vector lines map with a points map
    (connect operator), and by creating new lines between pairs of
    vector points (arcs operator).
    
    v.net offers two ways to add nodes to a network of arcs
    and one method to add arcs to a set of nodes.
    This tool implement one of them:
    
    Create nodes and arcs from a vector line/boundary file using the node
    operation. This is useful if you are mostly interested in the network
    itself and thus you can use intersections of the network as start and
    end points. Nodes will be created at all intersections of two or more
    lines. For an arc that consists of several segments connected by vertices
    (the typical case), only the starting and ending vertices are treated
    as network nodes.
    """
    
    from grass.pygrass.modules import Module
    
    m = Module(
        "v.net", input=networkFC, output=networkOUT,
        operation="nodes", arc_type='line',
        overwrite=True, run_=False
    )
    
    m()
    
    return networkOUT


def add_pnts_to_network(network, pntLyr, outNetwork, __threshold=200, asCMD=None):
    """
    Connect points to GRASS GIS Network
    """
    
    if not asCMD:
        from grass.pygrass.modules import Module
    
        m = Module(
            "v.net", input=network, points=pntLyr, operation="connect",
            threshold=__threshold, output=outNetwork, overwrite=True, run_=False
        )
    
        m()
    
    else:
        from gasp import exec_cmd
        
        rcmd = exec_cmd((
            "v.net input={} points={} operation=connect threshold={} "
            "output={} --overwrite --quiet"
        ).format(network, pntLyr, __threshold, outNetwork))
    
    return outNetwork



"""
Produce indicators
"""

def run_allpairs(network, fromToCol, toFromCol, outMatrix, arcLyr=1, nodeLyr=2,
                 asCMD=None):
    """
    Implementation of v.net.allpairs
    """
    
    if not asCMD:
        from grass.pygrass.modules import Module
    
        m = Module(
            "v.net.allpairs", input=network, output=outMatrix,
            arc_layer=arcLyr, node_layer=nodeLyr, arc_column=fromToCol,
            arc_backward_column=toFromCol, overwrite=True, run_=False
        )
    
        m()
    
    else:
        from gasp import exec_cmd
        
        rcmd = exec_cmd((
            "v.net.allpairs input={} output={} arc_layer={} "
            "node_layer={} arc_column={} arc_backward_column={} "
            "--overwrite --quiet"
        ).format(
            network, outMatrix, str(arcLyr), str(nodeLyr), fromToCol,
            toFromCol
        ))
    
    return outMatrix


def netpath(network, fileCats, fromToCol, toFromCol, outResult,
            arcLyr=1, nodeLyr=2):
    """
    Implementation of v.net.path
    """
    
    from grass.pygrass.modules import Module
    
    m = Module(
        "v.net.path", input=network, file=fileCats,
        output=outResult, arc_layer=arcLyr, node_layer=nodeLyr,
        arc_column=fromToCol, arc_backward_column=toFromCol,
        overwrite=True, run_=False
    )
    
    m()
    
    return outResult


def distance_between_catpoints(srcShp, facilitiesShp, networkShp, speedLimitCol,
                     onewayCol, grsWorkspace, grsLocation, outputShp):
    """
    Path bet points
    
    TODO: Work with files with cat
    """
    
    import os
    from gasp.oss       import get_filename
    from gasp.session   import run_grass
    from gasp.mng.gen   import merge_feat
    from gasp.prop.feat import feat_count
    
    # Merge Source points and Facilities into the same Feature Class
    SRC_NFEAT      = feat_count(srcShp, gisApi='pandas')
    FACILITY_NFEAT = feat_count(facilitiesShp, gisApi='pandas')
    
    POINTS = merge_feat([srcShp, facilitiesShp],
        os.path.join(os.path.dirname(outputShp), "points_net.shp"),
        api='pandas'
    )
    
    # Open an GRASS GIS Session
    gbase = run_grass(
        grsWorkspace, grassBIN="grass76",
        location=grsLocation, srs=networkShp
    )
    
    import grass.script       as grass
    import grass.script.setup as gsetup
    gsetup.init(gbase, grsWorkspace, grsLocation, 'PERMANENT')
    
    # Import GRASS GIS Module
    from gasp.to.shp.grs       import shp_to_grs
    from gasp.to.shp.grs       import grs_to_shp
    from gasp.cpu.grs.mng      import category
    from gasp.mng.grstbl       import add_field, add_table, update_table
    from gasp.mob.grstbx       import network_from_arcs
    from gasp.mob.grstbx       import add_pnts_to_network
    from gasp.mob.grstbx       import netpath
    from gasp.cpu.grs.mng.feat import geomattr_to_db
    from gasp.cpu.grs.mng.feat import copy_insame_vector
    
    # Add Data to GRASS GIS
    rdvMain = shp_to_grs(networkShp, get_filename(
        networkShp, forceLower=True))
    pntShp  = shp_to_grs(POINTS, "points_net")
    
    """Get closest facility layer:"""
    # Connect Points to Network
    newNetwork = add_pnts_to_network(rdvMain, pntShp, "rdv_points")
    
    # Sanitize Network Table and Cost Columns
    newNetwork = category(
        newNetwork, "rdv_points_time", "add",
        LyrN="3", geomType="line"
    )
    
    add_table(newNetwork, (
        "cat integer,kph double precision,length double precision,"
        "ft_minutes double precision,"
        "tf_minutes double precision,oneway text"
    ), lyrN=3)
    
    copy_insame_vector(newNetwork, "kph", speedLimitCol, 3, geomType="line")
    copy_insame_vector(newNetwork, "oneway",  onewayCol, 3, geomType="line")
    
    geomattr_to_db(
        newNetwork, "length", "length", "line",
        createCol=False, unit="meters", lyrN=3
    )
    
    update_table(newNetwork, "kph", "3.6", "kph IS NULL", lyrN=3)
    update_table(
        newNetwork, "ft_minutes",
        "(length * 60) / (kph * 1000.0)",
        "ft_minutes IS NULL", lyrN=3
    ); update_table(
        newNetwork, "tf_minutes",
        "(length * 60) / (kph * 1000.0)",
        "tf_minutes IS NULL", lyrN=3
    )
    
    # Exagerate Oneway's
    update_table(newNetwork, "ft_minutes", "1000", "oneway = 'TF'", lyrN=3)
    update_table(newNetwork, "tf_minutes", "1000", "oneway = 'FT'", lyrN=3)
    
    # Produce result
    result = netpath(
        newNetwork, "ft_minutes", "tf_minutes", get_filename(outputShp),
        arcLyr=3, nodeLyr=2
    )
    
    return grs_to_shp(result, outputShp, geomType="line", lyrN=3)

