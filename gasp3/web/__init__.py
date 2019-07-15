"""
Tools for web frameworks
"""

"""
E-mail related
"""

def email_exists(email):
    """
    Verify if a email exists using MailBoxLayer API
    
    
    """
    
    API_KEY = "b7bee0fa2b3ceb3408bd8245244b1479"
    
    URL = (
        "http://apilayer.net/api/check?access_key={}&email={}&"
        "smtp=1&format=1"
    ).format(API_KEY, str(email))
    
    jsonArray = json_fm_httpget(URL)
    
    return jsonArray["smtp_check"]

