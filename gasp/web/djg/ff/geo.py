"""
Deal with GeoData inside Django App
"""


def save_geodata(request, field_tag, folder):
    """
    Receive a file with vectorial geometry from a form field:
    
    Store the file in the server
    
    IMPORTANT: this method will only work if the FORM that is receiving the 
    files allows multiple files
    """
    
    import os
    from gasp.web.djg.ff import save_file
    
    files = request.FILES.getlist(field_tag)
    
    for f in files:
        save_file(folder, f)
    
    if len(files) > 1:
        shape = os.path.join(folder, '{f_name}.shp'.format(
            f_name = os.path.splitext(files[0].name)[0]
        ))
    
    else:
        shape = os.path.join(folder, files[0].name)
    
    return shape

