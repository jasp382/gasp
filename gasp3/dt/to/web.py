"""
WEB to Something
"""


def http_to_json(url):
    """
    Return a json object with the json data available in a URL
    """
    
    import urllib2
    import json
    
    web_response = urllib2.urlopen(url)
    
    read_page = web_response.read()
    
    json_data = json.loads(read_page)
    
    return json_data

