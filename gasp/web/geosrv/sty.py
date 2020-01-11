"""
Tools for Geoserver styles management
"""


def lst_styles(conf={
        'USER':'admin', 'PASSWORD': 'geoserver',
        'HOST':'localhost', 'PORT': '8888'
    }):
    """
    List Styles in Geoserver
    """
    
    import requests
    
    protocol = 'http' if 'PROTOCOL' not in conf else conf['PROTOCOL']
    
    url = '{pro}://{host}:{port}/geoserver/rest/styles'.format(
        host=conf['HOST'], port=conf['PORT'], pro=protocol
    )
    
    r = requests.get(
        url, headers={'Accept': 'application/json'},
        auth=(conf['USER'], conf['PASSWORD'])
    )
    
    styles = r.json()
    
    if 'style' in styles['styles']:
        return [style['name'] for style in styles['styles']['style']]
    
    else:
        return []


def del_style(name, conf={
        'USER':'admin', 'PASSWORD': 'geoserver',
        'HOST':'localhost', 'PORT': '8888'
    }):
    """
    Delete a specific style
    """
    
    import requests; import json
    
    protocol = 'http' if 'PROTOCOL' not in conf else conf['PROTOCOL']
    
    url = ('{pro}://{host}:{port}/geoserver/rest/styles/{stl}?'
           'recurse=true').format(
               host=conf['HOST'], port=conf['PORT'], stl=name, pro=protocol
           )
    
    r = requests.delete(url, auth=(conf['USER'], conf['PASSWORD']))
    
    return r


def create_style(name, sld, conf={
        'USER':'admin', 'PASSWORD': 'geoserver',
        'HOST':'localhost', 'PORT': '8888'
    }, overwrite=None):
    """
    Import SLD into a new Geoserver Style
    """

    import os
    import requests
    
    protocol = 'http' if 'PROTOCOL' not in conf else conf['PROTOCOL']
    
    if overwrite:
        GEO_STYLES = lst_styles(conf=conf)
        
        if name in GEO_STYLES:
            del_style(name, conf=conf)

    url = '{pro}://{host}:{port}/geoserver/rest/styles'.format(
        host=conf['HOST'], port=conf['PORT'], pro=protocol
    )

    xml = '<style><name>{n}</name><filename>{filename}</filename></style>'.format(
        n=name, filename=os.path.basename(sld)
    )

    r = requests.post(
        url,
        data=xml,
        headers={'content-type': 'text/xml'},
        auth=(conf['USER'], conf['PASSWORD'])
    )

    url = '{pro}://{host}:{port}/geoserver/rest/styles/{n}'.format(
        host=conf['HOST'], port=conf['PORT'], n=name, pro=protocol
    )

    with open(sld, 'rb') as f:

        r = requests.put(
            url,
            data=f,
            headers={'content-type': 'application/vnd.ogc.sld+xml'},
            auth=(conf['USER'], conf['PASSWORD'])
        )

        return r


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
    
    from gasp.web.geosrv.lyrs import lst_lyr
    
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

