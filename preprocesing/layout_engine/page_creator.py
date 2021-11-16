import os
import concurrent
from tqdm import tqdm

from .objects.page import Page
from .. import config_file as cfg


def create_page_from_files(data):
    page = Page()
    page.load_data(data[0])
    create_page([page, data[1], data[2]])


def create_page(data):
    """
    This function is used to render a single page from a metadata json file
    to a target location.

    :param paths:  a tuple of the page metadata and output path
    as well as whether or not to save the rendered file i.e. dry run or
    wet run

    :type paths: tuple
    """
    page = data[0]
    images_path = data[1]
    dry = data[2]

    filename = images_path+page.name+cfg.output_format
    if not os.path.isfile(filename) and not dry:
        img = page.render(show=False)
        img.convert("L").save(filename)


def render_pages(pages, images_dir, dry=False):
    """
    Takes pages and renders page images

    :param pages: A list of Page object

    :type metadata_dir: list -> Page

    :param images_dir: The output directory for the rendered pages

    :type images_dir: str
    """
    filenames = [(page, images_dir, dry)
                 for page in pages]

    with concurrent.futures.ProcessPoolExecutor() as executor:
        _ = list(tqdm(executor.map(create_page, filenames),
                      total=len(filenames)))


def render_pages_from_files(metadata_dir, images_dir, dry=False):
    """
    Takes metadata json files and renders page images

    :param metadata_dir: A directory containing all the metadata json files

    :type metadata_dir: str

    :param images_dir: The output directory for the rendered pages

    :type images_dir: str
    """
    filenames = [(metadata_dir+filename, images_dir, dry)
                 for filename in os.listdir(metadata_dir)
                 if filename.endswith(".json")]

    with concurrent.futures.ProcessPoolExecutor() as executor:
        _ = list(tqdm(executor.map(create_page_from_files, filenames),
                      total=len(filenames)))
