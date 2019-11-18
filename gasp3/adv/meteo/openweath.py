"""
Open Weather Map API
"""

API_KEY = '2ad19221a69d566f59ee3306f50ed69d'


def conditions_by_position(lat, lng):
    """
    Get Climatic conditions for sensor in some position
    """
    
    from gasp3.pyt.web import http_to_json
    
    URL = (
        "https://api.openweathermap.org/data/2.5/weather?lat={}&lon={}"
        "&appid={}"
    ).format(str(lat), str(lng), API_KEY)
    
    data = http_to_json(URL)
    
    return data
