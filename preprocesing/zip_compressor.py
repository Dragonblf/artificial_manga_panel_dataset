from zipfile import ZipFile


def unzip_file(from_path, to_path):
    """
    Unzip a file
    """
    with ZipFile(from_path, 'r') as f:
        f.extractall(to_path)


def zip_files(paths, to_path):
    """
    Compress files to zip file
    """
    with ZipFile(to_path, 'w') as f:
        for path in paths:
            f.write(path)
