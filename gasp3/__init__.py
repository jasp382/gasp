"""
GASP Python Package
"""

def exec_cmd(cmd):
    """
    Execute a command and provide information about the results
    """
    import subprocess
    
    p = subprocess.Popen(cmd, shell=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    out, err = p.communicate()
    
    if p.returncode != 0:
        raise ValueError(
            'Output: {o}\nError: {e}'.format(o=str(out), e=str(err))
        )
    
    else:
        return out


def goToList(obj):
    """
    A method uses a list but the user gives a str
    
    This method will see if the object is a str and convert it to a list
    """
    
    return [obj] if type(obj) == str else obj \
        if type(obj) == list else None

