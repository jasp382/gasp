"""
Tools for Geoserver workspaces management
"""


def lst_ws(conf={
    'USER':'admin', 'PASSWORD': 'geoserver',
    'HOST':'localhost', 'PORT': '8080'}):
    """
    Return a list with all avaiable workspaces in the GeoServer
    """
    
    import requests
    
    protocol = 'http' if 'PROTOCOL' not in conf else conf['PROTOCOL']

    url = '{pro}://{host}:{port}/geoserver/rest/workspaces'.format(
        host=conf['HOST'], port=conf['PORT'], pro=protocol
    )

    r = requests.get(
        url, headers={'Accept': 'application/json'},
        auth=(conf['USER'], conf['PASSWORD'])
    )

    workspaces = r.json()
    if 'workspace' in workspaces['workspaces']:
        return [w['name'] for w in workspaces['workspaces']['workspace']]
    else:
        return []


def del_ws(name, conf={
        'USER':'admin', 'PASSWORD': 'geoserver',
        'HOST':'localhost', 'PORT': '8080'}):
    """
    Delete an existing GeoServer Workspace 
    """
    
    import requests
    import json
    
    protocol = 'http' if 'PROTOCOL' not in conf else conf['PROTOCOL']

    url = ('{pro}://{host}:{port}/geoserver/rest/workspaces/{work}?'
           'recurse=true').format(
               host=conf['HOST'], port=conf['PORT'], work=name,
               pro=protocol
           )

    r = requests.delete(
        url,
        auth=(conf['USER'], conf['PASSWORD'])
    )

    return r


def create_ws(name, conf={
        'USER':'admin', 'PASSWORD': 'geoserver',
        'HOST':'localhost', 'PORT': '8080'
    }, overwrite=True):
    """
    Create a new Geoserver Workspace
    """
    
    import requests
    import json
    
    protocol = 'http' if 'PROTOCOL' not in conf else conf['PROTOCOL']

    url = '{pro}://{host}:{port}/geoserver/rest/workspaces'.format(
        host=conf['HOST'], port=conf['PORT'], pro=protocol
    )
    
    if overwrite:
        GEO_WORK = lst_ws(conf=conf)
        if name in GEO_WORK:
            del_ws(name, conf=conf)

    r = requests.post(
        url,
        data=json.dumps({'workspace': {'name' : name}}),
        headers={'content-type': 'application/json'},
        auth=(conf['USER'], conf['PASSWORD'])
    )

    return r

