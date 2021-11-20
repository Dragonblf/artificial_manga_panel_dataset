import os
import concurrent

import paths

from tqdm import tqdm
from .. import config_file as cfg


def create_page(data):
    """
    This function is used to render a single page from a metadata json file
    to a target location.

    :param data:  a tuple of the page metadata and output path
    as well as whether or not to save the rendered file i.e. dry run or
    wet run

    :type paths: tuple
    """
    page, dry = data
    filename = paths.GENERATED_IMAGES_FOLDER + page.name + cfg.output_format
    if not os.path.isfile(filename) and not dry:
        img = page.render(show=False)
        img.convert("L").save(filename)


def render_pages(pages, dry=False):
    """
    Takes pages and renders page images

    :param pages: A list of Page object
    """
    filenames = [(page, dry) for page in pages]
    with concurrent.futures.ProcessPoolExecutor() as executor:
        _ = list(tqdm(executor.map(create_page, filenames),
                      total=len(filenames)))
