"""
Apply Indexes to highligh LULC types in Satellite Imagery
"""

def ndwi2(green, nir, outRst, toReflectance=10000):
    """
    Apply Normalized Difference Water Index
    
    In Sentinel L2 Products, the raster value is the Reflectance
    multiplied by 10000, so to get the real reflectance, we have to apply:
    rst / 10000... toReflectance are the 10000 value in this example
    
    EXPRESSION: ((green / toReflectance) - (nir /toReflectance)) / 
    ((green / toReflectance) + (nir /toReflectance))
    """
    
    return outRst

