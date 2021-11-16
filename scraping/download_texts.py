# Download dataset JESC from website and extract it
import requests
import os
from tqdm import tqdm
import tarfile
import paths


def download_file(url, filepath):
    """
    Download JESC dataset

    :param url: URL of file to download

    :type url: str

    :param filepath: Location to download file to

    :type filepath: str
    """
    # NOTE the stream=True parameter below
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        # total_length = r.headers.get('content-length')
        # total_length = int(total_length)

        # Content-Length is returned wrong
        total_length = int(99803000/1024)
        with open(filepath, 'wb') as f:
            for data in tqdm(r.iter_content(chunk_size=1024),
                             total=total_length,
                             unit='KB',
                             unit_scale=False,
                             unit_divisor=1024
                             ):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                f.write(data)


def download_and_extract_jesc():
    """
    Downloads the Japanese English Subtitle Corpus
    and places it into datasets/text_dataset/
    """
    url = "https://nlp.stanford.edu/projects/jesc/data/raw.tar.gz"
    filepath = paths.DATASET_TEXT_RAW_JESC_DIALOGUES_FILE
    if os.path.isfile(filepath):
        print("File already exists")
    else:
        print("Downloading JESC text corpus")
        download_file(url, filepath)

    text_dataset_dir = paths.DATASET_TEXT_FOLDER
    if not os.path.isdir(text_dataset_dir):
        os.mkdir(text_dataset_dir)

    print("Extracting archive now!")
    tar_arch = tarfile.open(filepath)
    tar_arch.extractall(text_dataset_dir)
    tar_arch.close()

    os.rename(text_dataset_dir+"raw/raw", text_dataset_dir+"raw.txt")
    os.removedirs(text_dataset_dir+"raw/")
