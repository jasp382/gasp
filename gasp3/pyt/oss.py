"""
Methods to interact with the Operating System
"""

import os

def os_name():
    import platform
    return str(platform.system())


def get_filename(__file, forceLower=None):
    """
    Return filename without file format
    """
    
    filename = os.path.splitext(os.path.basename(__file))[0]
    
    if forceLower:
        filename = filename.lower()
    
    return filename

def get_fileformat(__file):
    """
    Return file format
    """
    
    return os.path.splitext(__file)[1]


def get_filesize(path, unit='MB'):
    """
    Return file size in some menory unit
    """
    
    memory = os.path.getsize(path)
    
    if unit == 'MB':
        memory = (memory / 1024.0) /1024
    
    elif unit == 'KB':
        memory = memory / 1024.0
    
    else:
        memory = memory
    
    return memory

def list_files(w, file_format=None, filename=None):
    """
    List the abs path of all files with a specific extension on a folder
    """
    
    from gasp3 import goToList
    
    # Prepare file format list
    if file_format:
        formats = goToList(file_format)
        
        for f in range(len(formats)):
            if formats[f][0] != '.':
                formats[f] = '.' + formats[f]
    
    # List files
    r = []
    for (d, _d_, f) in os.walk(w):
        r.extend(f)
        break
    
    # Filter files by format or not
    if not file_format:
        t = [os.path.join(w, i) for i in r]
    
    else:
        t = [
            os.path.join(w, i) for i in r
            if os.path.splitext(os.path.basename(i))[1] in formats
        ]
    
    # Filter by filename
    if not filename:
        return t
    
    else:
        filename = goToList(filename)
        
        _t = []
        for i in t:
            if get_filename(i) in filename:
                _t.append(i)
        
        return _t


def list_folders(w, name=None):
    """
    List folders path or name in one folder
    """
    
    foldersname = []
    for (dirname, dirsname, filename) in os.walk(w):
        foldersname.extend(dirsname)
        break
    
    if name:
        return foldersname
    
    else:
        return [os.path.join(w, fld) for fld in foldersname]


def list_folders_files(w, name=None):
    """
    List folders and files path or name
    """
    
    fld_file = []
    for (dirname, dirsname, filename) in os.walk(w):
        fld_file.extend(dirsname)
        fld_file.extend(filename)
        break
    
    if name:
        return fld_file
    
    else:
        return [os.path.join(w, f) for f in fld_file]


def list_folders_subfiles(path, files_format=None,
                          only_filename=None):
    """
    List folders in path and the files inside each folder
    """
    
    folders_in_path = list_folders(path)
    
    out = {}
    for folder in folders_in_path:
        out[folder] = list_files(
            folder, file_format=files_format
        )
        
        if only_filename:
            for i in range(len(out[folder])):
                out[folder][i] = os.path.basename(out[folder][i])
    
    return out

"""
Manage folders
"""

def create_folder(folder, randName=None, overwrite=True):
    """
    Create a new folder
    Replace the given folder if that one exists
    """
    
    if randName:
        import random
        chars = '0123456789qwertyuiopasdfghjklzxcvbnm'
        
        name = ''
        for i in range(10):
            name+=random.choice(chars)
        
        folder = os.path.join(folder, name)
    
    if os.path.exists(folder):
        if overwrite:
            import shutil
            
            shutil.rmtree(folder)
        else:
            raise ValueError(
                "{} already exists".format(folder)
            )
    
    os.mkdir(folder)
    
    return folder


def del_folder(folder):
    """
    Delete folder if exists
    """
    
    import shutil
    
    if os.path.exists(folder) and os.path.isdir(folder):
        shutil.rmtree(folder)


"""
Delete things
"""

def del_file(_file):
    """
    Delete files if exists
    """
    
    from gasp3 import goToList
    
    for ff in goToList(_file):
        if os.path.isfile(ff) and os.path.exists(ff):
            os.remove(ff)



def del_file_folder_tree(fld, file_format):
    """
    Delete all files with a certain format in a folder and sub-folders
    """
    
    if file_format[0] != '.':
        file_format = '.' + file_format
    
    for (dirname, sub_dir, filename) in os.walk(fld):
        for f in filename:
            if os.path.splitext(f)[1] == file_format:
                os.remove(os.path.join(dirname, f))


def del_files_by_name(folder, names):
    """
    Del files with some name
    """
    
    
    lst_files = list_files(folder, filename=basenames)
    
    for f in lst_files:
        del_file(f)


def del_files_by_partname(folder, partname):
    """
    If one file in 'folder' has 'partname' in his name, it will be
    deleted
    """
    
    files = list_files(folder)
    
    for _file in files:
        if partname in os.path.basename(_file):
            del_file(_file)


"""
Rename things
"""

def rename_files_with_same_name(folder, oldName, newName):
    """
    Rename files in one folder with the same name
    """
    
    _Files = list_files(folder, filename=oldName)
    
    Renamed = []
    for f in _Files:
        newFile = os.path.join(folder, newName + get_fileformat(f))
        os.rename(f, newFile)
        
        Renamed.append(newFile)
    
    return Renamed


def onFolder_rename(fld, toBeReplaced, replacement, only_files=True,
                    only_folders=None):
    """
    List all files in a folder; see if the filename includes what is defined
    in the object 'toBeReplaced' and replace this part with what is in the
    object 'replacement'
    """
    
    from gasp.oss import list_files

    if not only_files and not only_folders:
        files = list_folders_files(fld)

    elif not only_files and only_folders:
        files = list_folders(fld)

    elif only_files and not only_folders:
        files = list_files(fld)

    for __file in files:
        if os.path.isfile(__file):
            filename = os.path.splitext(os.path.basename(__file))[0]
        else:
            filename = os.path.basename(__file)

        if toBeReplaced in filename:
            renamed = filename.replace(toBeReplaced, replacement)

            if os.path.isfile(__file):
                renamed = renamed + os.path.splitext(os.path.basename(__file))[1]

            os.rename(
                __file, os.path.join(os.path.dirname(__file), renamed)
            )


def onFolder_rename2(folder, newBegin, stripStr, fileFormats=None):
    """
    Erase some characters of file name and add something to the
    begining of the file
    """
    
    files = list_files(folder, file_format=fileFormats)
    
    for _file in files:
        name = get_filename(_file, forceLower=True)
        
        new_name = name.replace(stripStr, '')
        new_name = "{}{}{}".format(newBegin, new_name, get_fileformat(_file))
        
        os.rename(_file, os.path.join(os.path.dirname(_file), new_name))


"""
Copy Things
"""

def copy_file(src, dest):
    """
    Copy a file
    """
    
    from shutil import copyfile
    
    copyfile(src, dest)
    
    return dest


"""
Specific Utils to manage data in folders
"""

def identify_groups(folder, splitStr, groupPos, outFolder):
    """
    Identifica o grupo a que um ficheiro pertence e envia-o para uma nova
    pasta com os ficheiros que pertencem a esse grupo.
    
    Como e que o grupo e identificado?
    * O nome do ficheiro e partido em dois em funcao de splitStr;
    * O groupPos identifica qual e a parte (primeira ou segunda) que 
    corresponde ao grupo.
    """
    
    files = list_files(folder)
    
    # List groups and relate files with groups:
    groups = {}
    for _file in files:
        # Split filename
        filename = os.path.splitext(os.path.basename(_file))[0]
        fileForm = os.path.splitext(os.path.basename(_file))[1]
        group = filename.split(splitStr)[groupPos]
        namePos = 1 if not groupPos else 0
        
        if group not in groups:
            groups[group] = [[filename.split(splitStr)[namePos], fileForm]]
        else:
            groups[group].append([filename.split(splitStr)[namePos], fileForm])
    
    # Create one folder for each group and put there the files related
    # with that group.
    for group in groups:
        group_folder = create_folder(os.path.join(outFolder, group))
            
        for filename in groups[group]:
            copy_file(
                os.path.join(folder, '{a}{b}{c}{d}'.format(
                    a=filename[0], b=splitStr, c=group,
                    d=filename[1]
                )),
                os.path.join(group_folder, '{a}{b}'.format(
                    a=filename[0], b=filename[1]
                ))
            )

