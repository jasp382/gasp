"""
Read NC Files
"""

def get_nc_dim_var(ncObj, justVar=None, justDim=None):
    """
    Get Variables and Dimensions in NC file
    """
    
    if justVar and not justDim:
        return ncObj.variables
    elif not justVar and justDim:
        return ncObj.dimensions
    else:
        return {
            'VARIABLES' : ncObj.variables, 'DIMENSIONS' : ncObj.dimensions
        }

