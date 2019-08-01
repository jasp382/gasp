"""
Design style to layers
"""


def assign_style_to_layer(style, layer, conf={
        'USER':'admin', 'PASSWORD': 'geoserver',
        'HOST':'localhost', 'PORT': '8080'
    }, protocol='http'):
    """
    Add a style to a geoserver layer
    """

    import requests
    import json

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
    }, protocol='http'):
    """
    Add a style to all layers with the same basename
    """

    # List layers that starts with a certain basename
    layers = list_layers(conf=conf, protocol=protocol)

    for lyr in layers:
        if basename in lyr:
            # Apply style to all layers in flayers
            r = add_style_to_layer(style, lyr, conf=conf, protocol=protocol)


def add_style_to_layers(layers, style, conf={
        'USER':'admin', 'PASSWORD': 'geoserver',
        'HOST':'localhost', 'PORT': '8888'
    }, protocol='http'):
    """
    Add a style to all layers in a list
    """
    
    for layer in layers:
        r = add_style_to_layer(style, layer, conf=conf, protocol=protocol)

