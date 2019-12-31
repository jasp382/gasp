"""
Python Objects Handling
"""

def obj_to_lst(obj):
    """
    A method uses a list but the user gives a str
    
    This method will see if the object is a str and convert it to a list
    """
    
    return [obj] if type(obj) == str else obj \
        if type(obj) == list else None