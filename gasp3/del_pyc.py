if __name__ == "__main__":
    from gasp.oss.ops import del_file_folder_tree
    import os
    
    del_file_folder_tree(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'pyc'
    )