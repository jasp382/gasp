"""
Dominating Geoserver with Python and requests

* the following methods may be used in Linux and MSWindows
"""


def backup(backup_file, conf={
    'USER':'admin', 'PASSWORD': 'geoserver',
    'HOST':'localhost', 'PORT': '8080'
    }, protocol='http'):
    """
    """
    
    import requests
    import json
    
    url = '{pro}://{host}:{port}/geoserver/rest/br/backup/'.format(
        host=conf['HOST'], port=conf['PORT'], pro=protocol
    )
    
    backup_parameters = {
        "backup" : {
            "archiveFile" : backup_file,
            "overwrite":True,
            "options": {
                #"option": ["BK_BEST_EFFORT=true"]
            }
            # filter
        }
    }   
    
    r = requests.post(
        url, headers={'content-type': 'application/json'},
        data=json.dumps(backup_parameters),
        auth=(conf['USER'], conf['PASSWORD'])
    )
    
    return r