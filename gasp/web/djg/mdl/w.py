"""
Write in Models
"""

def update_model(model, data):
    """
    Update Model Data
    """
    
    from gasp import __import
    
    djangoCls = __import(model)
    __model = djangoCls()
    
    for row in data:
        for k in row:
            setattr(__model, k, row[k])
        __model.save()

