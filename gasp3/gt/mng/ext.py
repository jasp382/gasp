"""
Operations based on extent
"""

"""
GeoPandas Related
"""


def df_add_ext(df, geomCol):
    """
    Add minx, miny, maxx, maxy to dataframe
    """
    
    return df.merge(
        df[geomCol].bounds, how='inner',
        left_index=True, right_index=True
    )

