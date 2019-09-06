"""
Tools for Geoserver workspaces management
"""


def list_workspaces(conf={
    'USER':'admin', 'PASSWORD': 'geoserver',
    'HOST':'localhost', 'PORT': '8080'
    }, protocol='http'):
    """
    Return a list with all avaiable workspaces in the GeoServer
    """
    
    import requests

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


def del_workspace(name, conf={
        'USER':'admin', 'PASSWORD': 'geoserver',
        'HOST':'localhost', 'PORT': '8080'
    }, protocol='http'):
    """
    Delete an existing GeoServer Workspace 
    """
    
    import requests
    import json

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


def create_workspace(name, conf={
        'USER':'admin', 'PASSWORD': 'geoserver',
        'HOST':'localhost', 'PORT': '8080'
    }, overwrite=True, protocol='http'):
    """
    Create a new Geoserver Workspace
    """
    
    import requests
    import json

    url = '{pro}://{host}:{port}/geoserver/rest/workspaces'.format(
        host=conf['HOST'], port=conf['PORT'], pro=protocol
    )
    
    if overwrite:
        GEO_WORK = list_workspaces(conf=conf, protocol=protocol)
        if name in GEO_WORK:
            del_workspace(name, conf=conf, protocol=protocol)

    r = requests.post(
        url,
        data=json.dumps({'workspace': {'name' : name}}),
        headers={'content-type': 'application/json'},
        auth=(conf['USER'], conf['PASSWORD'])
    )

    return r

