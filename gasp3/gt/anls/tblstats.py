"""
Table Statistics
"""

def tbl_to_areamtx(inShp, col_a, col_b, outXls):
    """
    Table to Matrix
    
    Table as:
        FID | col_a | col_b | geom
    0 |  1  |   A   |   A   | ....
    0 |  2  |   A   |   B   | ....
    0 |  3  |   A   |   A   | ....
    0 |  4  |   A   |   C   | ....
    0 |  5  |   A   |   B   | ....
    0 |  6  |   B   |   A   | ....
    0 |  7  |   B   |   A   | ....
    0 |  8  |   B   |   B   | ....
    0 |  9  |   B   |   B   | ....
    0 | 10  |   C   |   A   | ....
    0 | 11  |   C   |   B   | ....
    0 | 11  |   C   |   D   | ....
    
    To:
    classe | A | B | C | D
       A   |   |   |   | 
       B   |   |   |   |
       C   |   |   |   |
       D   |   |   |   |
    
    col_a = rows
    col_b = cols
    """
    
    import pandas as pd
    import numpy  as np
    from gasp3.fm import tbl_to_obj
    from gasp3.to import obj_to_tbl
    
    # Open data
    df = tbl_to_obj(inShp)
    
    # Get Area
    df['realarea'] = df.geometry.area
    
    # Get rows and Cols
    rows = list(np.sort(df[col_a].unique()))
    cols = list(np.sort(df[col_b].unique()))
    
    # Produce matrix
    outDf = []
    for row in rows:
        newCols = [row]
        for col in cols:
            newDf = df[(df[col_a] == row) & (df[col_b] == col)]
            
            area = newDf.realarea.sum()
            
            newCols.append(area)
        
        outDf.append(newCols)
    
    outcols = ['class'] + cols
    outDf = pd.DataFrame(outDf, columns=outcols)
    
    # Export to Excel
    return obj_to_tbl(outDf, outXls)

