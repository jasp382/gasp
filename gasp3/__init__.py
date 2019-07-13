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

def random_str(char_number, all_char=None):
    """
    Generates a random string with numbers and characters
    """
    
    import random as r
    import string
    
    char = string.digits + string.ascii_letters
    if all_char:
        char += string.punctuation
    
    rnd = ''
    
    for i in range(char_number): rnd += r.choice(char)
    
    return rnd
