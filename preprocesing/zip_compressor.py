from zipfile import ZipFile
from .multiprocessing import open_pool


def unzip_file(from_path, to_path):
    """
    Unzip a file
    """
    with ZipFile(from_path, 'r') as f:
        f.extractall(to_path)


def _write_zip(data):
    path, to_path = data
    with ZipFile(to_path, 'w') as f:
        f.write(path)


def zip_files(paths, to_path):
    """
    Compress files to zip file
    """
    files = [(path, to_path) for path in paths]
    open_pool(_write_zip, files)
