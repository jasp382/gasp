"""
Get web responses
"""


def json_fm_httpget(url):
    """
    Return a json object with the json data available in a URL
    """
    
    import urllib2
    import json
    
    web_response = urllib2.urlopen(url)
    
    read_page = web_response.read()
    
    json_data = json.loads(read_page)
    
    return json_data


def data_from_get(url, getParams):
    """
    Return json from URL - GEST Request
    """
    
    import json
    import requests
    
    response = requests.get(url=url, params=getParams)
    
    return json.loads(response.text)


def data_from_post(url, postdata, head='application/json'):
    """
    Return data retrieve by a POST Request
    """
    
    import json
    import requests
    
    r = requests.post(
        url, data=json.dumps(postdata),
        headers={'content-type' : head}
    )
    
    return r.json()