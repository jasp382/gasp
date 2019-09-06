"""
Compress files with Python
"""


def tar_compress_folder(tar_fld, tar_file):
    """
    Compress a given folder
    """
    
    from gasp3 import exec_cmd
    
    cmd = 'cd {p} && tar -czvf {tar_f} {fld}'.format(
        tar_f=tar_file, fld=str(os.path.basename(tar_fld)),
        p=str(os.path.dirname(tar_fld))
    )
    
    code, out, err = exec_cmd(cmd)
    
    return tar_file


def zip_files(lst_files, zip_file):
    """
    Zip all files in the lst_files
    """
    
    import zipfile
    import os
    
    __zip = zipfile.ZipFile(zip_file, mode='w')
    
    for f in lst_files:
        __zip.write(f, os.path.relpath(f, os.path.dirname(zip_file)),
                       compress_type=zipfile.ZIP_DEFLATED)
    
    __zip.close()


def zip_folder(folder, zip_file):
    from gasp3.pyt.oss import list_files
    
    files = list_files(folder)
    
    zip_files(files, zip_file)

