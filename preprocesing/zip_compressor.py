from zipfile import ZipFile
from tqdm import tqdm


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
        for path in tqdm(paths):
            f.write(path)
        f.close()
