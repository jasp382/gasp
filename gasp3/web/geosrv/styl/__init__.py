"""
Tools for Geoserver styles management
"""


def list_styles(conf={
        'USER':'admin', 'PASSWORD': 'geoserver',
        'HOST':'localhost', 'PORT': '8888'
    }, protocol='http'):
    """
    List Styles in Geoserver
    """
    
    import requests
    
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
    }, protocol='http'):
    """
    Delete a specific style
    """
    
    import requests
    import json
    
    url = ('{pro}://{host}:{port}/geoserver/rest/styles/{stl}?'
           'recurse=true').format(
               host=conf['HOST'], port=conf['PORT'], stl=name, pro=protocol
           )
    
    r = requests.delete(url, auth=(conf['USER'], conf['PASSWORD']))
    
    return r


def create_style(name, sld, conf={
        'USER':'admin', 'PASSWORD': 'geoserver',
        'HOST':'localhost', 'PORT': '8888'
    }, overwrite=None, protocol='http'):
    """
    Import SLD into a new Geoserver Style
    """

    import os
    import requests
    
    if overwrite:
        GEO_STYLES = list_styles(conf=conf, protocol=protocol)
        
        if name in GEO_STYLES:
            del_style(name, conf=conf, protocol=protocol)

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

