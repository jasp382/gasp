"""
Tools for Geoserver layers management
"""


def lst_lyr(conf={
    'USER':'admin', 'PASSWORD': 'geoserver',
    'HOST':'localhost', 'PORT': '8080'
    }):
    """
    List all layers in the geoserver
    """

    import requests
    
    protocol = 'http' if 'PROTOCOL' not in conf else conf['PROTOCOL'] 

    url = '{pro}://{host}:{port}/geoserver/rest/layers'.format(
        host=conf['HOST'], port=conf['PORT'], pro=protocol
    )

    r = requests.get(
        url, headers={'Accept': 'application/json'},
        auth=(conf['USER'], conf['PASSWORD'])
    )

    layers = r.json()

    return [l['name'] for l in layers['layers']['layer']]


def pub_pglyr(workspace, store, pg_table, title=None, gs_con={
        'USER':'admin', 'PASSWORD': 'geoserver',
        'HOST':'localhost', 'PORT': '8888'
    }):
    """
    Publish PostGIS table in geoserver
    """
    
    import os;         import requests
    from gasp.pyt.char import random_str
    from gasp.pyt.Xml  import write_xml_tree
    from gasp.pyt.oss  import create_folder, del_folder
    
    protocol = 'http' if 'PROTOCOL' not in gs_con else gs_con['PROTOCOL']
    
    # Create folder to write xml
    wTmp = create_folder(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)), random_str(7)
        )
    )
    
    # Create obj with data to be written in the xml
    lyr_title = "Title {}".format(pg_table) if not title else title
    elements = {
        "featureType": {
            "name"  : pg_table,
            "title" : lyr_title
        }
    }
    
    # Write the xml
    xml_file = write_xml_tree(
        elements,
        os.path.join(wTmp, '{}.xml'.format(pg_table))
    )
    
    # Create Geoserver Layer
    url = (
        '{pro}://{host}:{port}/geoserver/rest/workspaces/{wname}/'
        'datastores/{store_name}/featuretypes'
    ).format(
        host=gs_con['HOST'], port=gs_con['PORT'], wname=workspace,
        store_name=store, pro=protocol
    )
    
    with open(xml_file, 'rb') as __xml:
        r = requests.post(
            url, data=__xml, headers={'content-type': 'text/xml'},
            auth=(gs_con['USER'], gs_con['PASSWORD'])
        )
        
        __xml.close()
    
    del_folder(wTmp)
    
    return r


def pub_rst_lyr(layername, datastore, workspace, epsg_code, conf={
        'USER': 'admin', 'PASSWORD': 'geoserver',
        'HOST': 'localhost', 'PORT': '8888'
    }):
    """
    Publish a Raster layer
    """
    
    import os;            import requests
    from gasp.pyt.char    import random_str
    from gasp.pyt.Xml     import write_xml_tree
    from gasp.pyt.oss     import create_folder, del_folder
    from gasp.gt.prop.prj import epsg_to_wkt
    
    protocol = 'http' if 'PROTOCOL' not in conf else conf['PROTOCOL']
    
    url = (
        '{pro}://{host}:{port}/geoserver/rest/workspaces/{work}/'
        'coveragestores/{storename}/coverages'
    ).format(
        host=conf['HOST'], port=conf['PORT'],
        work=workspace, storename=datastore, pro=protocol
    )
    
    # Create obj with data to be written in the xml
    xmlTree = {
        "coverage" : {
            "name"      : layername,
            "title"     : layername,
            "nativeCRS" : str(epsg_to_wkt(epsg_code)),
            "srs"       : 'EPSG:{}'.format(str(epsg_code)),
        }
    }
    
    # Write XML
    wTmp = create_folder(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            random_str(7)
        )
    ) 
    
    xml_file = write_xml_tree(
        xmlTree, os.path.join(wTmp, 'rst_lyr.xml')
    )
    
    # Create layer
    with open(xml_file, 'rb') as f:
        r = requests.post(
            url, data=f,
            headers={'content-type': 'text/xml'},
            auth=(conf['USER'], conf['PASSWORD'])
        )
    
    del_folder(wTmp)
    
    return r


def del_lyr(lyr, conf={
        'USER':'admin', 'PASSWORD': 'geoserver',
        'HOST':'localhost', 'PORT': '8080'
    }):
    """
    Delete some layer
    """
    
    import requests
    
    protocol = 'http' if 'PROTOCOL' not in conf else conf['PROTOCOL']
    
    url = '{}://{}:{}/geoserver/rest/layers/{}'.format(
        protocol, conf["HOST"], conf["PORT"], lyr
    )
    
    r = requests.delete(url, auth=(conf["USER"], conf["PASSWORD"]))
    
    return r

