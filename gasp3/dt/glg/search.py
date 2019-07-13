"""
Programatic Search using Google Search Engine
"""


def exec_search(keyword, __site=None, NRESULTS=10):
    """
    Get Links returned by Google using some keyword
    """
    
    from googlesearch import search
    
    Q = keyword if not __site else "site:{} {}".format(__site, keyword)
    
    searchCls = search(
        Q,
        tld='com', lang='pt',#tbs, safe,
        num=NRESULTS, start=0, stop=None,
        #domains, only_standard, extra_params, tpe, user_agent,
        pause=2.0
    )
    
    return [str(j) for j in searchCls]

