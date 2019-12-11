"""
Extraction Operations using OSM Data
"""


def select_highways(inOsm, outOsm):
    """
    Extract some tag from OSM file
    """
    
    import os
    from gasp3 import exec_cmd
    
    outExt = os.path.splitext(outOsm)[1]
    
    cmd = (
        'osmosis --read-xml enableDateParsing=no file={} --tf accept-ways '
        'highway=* --used-node --write-{} {}' 
    ).format(
        inOsm,
        "pbf" if outExt == ".pbf" else "xml", outOsm)
    
    outcmd = exec_cmd(cmd)
    
    return outOsm
