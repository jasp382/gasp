"""
Get Files from the Internet
"""


def get_file_ul(url, output):
    """
    Return a file from the web and save it somewhere
    """
    
    import urllib
    
    data_file = urllib.URLopener()
    
    data_file.retrieve(url, output)
    
    return output


def get_file(url, output):
    """
    Save content of url
    """
    
    import requests
    
    r = requests.get(url, allow_redirects=True)
    
    with open(output, 'wb') as f:
        f.write(r.content)
    
    return output


def get_file_via_scp(host, username, hostpath, outpath, privateKey=None):
    """
    Get file from remote sensing via SCP
    """
    
    from gasp3 import exec_cmd
    
    outcmd = exec_cmd("scp {}{}@{}:{} {}".format(
        "-i {} ".format(privateKey) if privateKey else "",
        username, host, hostpath, outpath
    ))