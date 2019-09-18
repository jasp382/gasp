"""
Design style to layers
"""


def assign_style_to_layer(style, layer, conf={
        'USER':'admin', 'PASSWORD': 'geoserver',
        'HOST':'localhost', 'PORT': '8080'
    }):
    """
    Add a style to a geoserver layer
    """

    import requests
    import json
    
    protocol = 'http' if not 'PROTOCOL' in conf else conf['PROTOCOL']

    url = '{pro}://{host}:{port}/geoserver/rest/layers/{lyr}/styles'.format(
        host=conf['HOST'], port=conf['PORT'], lyr=layer, pro=protocol
    )

    r = requests.post(
        url,
        data=json.dumps({'style' : {'name': style}}),
        headers={'content-type': 'application/json'},
        auth=(conf['USER'], conf['PASSWORD'])
    )

    return r


def add_style_to_layers_basename(style, basename, conf={
        'USER':'admin', 'PASSWORD': 'geoserver',
        'HOST':'localhost', 'PORT': '8888'
    }):
    """
    Add a style to all layers with the same basename
    """
    
    from gasp3.web.geosrv.lyrs import lst_lyr
    
    protocol = 'http' if not 'PROTOCOL' in conf else conf['PROTOCOL']

    # List layers that starts with a certain basename
    layers = lst_lyr(conf=conf)

    for lyr in layers:
        if basename in lyr:
            # Apply style to all layers in flayers
            r = assign_style_to_layer(style, lyr, conf=conf)


def add_style_to_layers(layers, style, conf={
        'USER':'admin', 'PASSWORD': 'geoserver',
        'HOST':'localhost', 'PORT': '8888'
    }):
    """
    Add a style to all layers in a list
    """
    
    for layer in layers:
        r = assign_style_to_layer(style, layer, conf=conf)

