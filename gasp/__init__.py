"""
GASP Python Package
"""

def __import(full_path):
    """
    For 'gasp.gt.module', return the 'module' object
    """
    
    components = full_path.split('.')
    mod = __import__(components[0])
    
    for comp in components[1:]:
        mod = getattr(mod, comp)
    
    return mod


def exec_cmd(cmd):
    """
    Execute a command and provide information about the results
    """
    import subprocess
    
    p = subprocess.Popen(cmd, shell=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    out, err = p.communicate()
    
    if p.returncode != 0:
        print(cmd)
        raise ValueError(
            'Output: {o}\nError: {e}'.format(
                o=out.decode('utf-8'), e=err.decode('utf-8')
            )
        )
    
    else:
        return out.decode('utf-8')

