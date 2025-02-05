import os
import paths

from .. import config_file as cfg
from ..multiprocessing import open_pool


def create_page_bw(data):
    """
    This function is used to render a single page from a metadata json file
    to a target location in black and white.

    :param data:  a tuple of the page metadata and output path
    as well as whether or not to save the rendered file i.e. dry run or
    wet run

    :type paths: tuple
    """
    try:
        page, dry = data
        filenameBW = paths.GENERATED_IMAGES_FOLDER + page.name + "_BW" + cfg.output_format
        if not os.path.isfile(filenameBW) and not dry:
            img = page.render(show=False)
            img.convert("L").save(filenameBW, cfg.pil_compression,
                                  optimize=True, quality=cfg.compression_quality)
    except:
        print("We couldn't render " + filenameBW)


def create_page_colored(data):
    """
    This function is used to render a single page from a metadata json file
    to a target location with colors.

    :param data:  a tuple of the page metadata and output path
    as well as whether or not to save the rendered file i.e. dry run or
    wet run

    :type paths: tuple
    """
    try:
        page, dry = data
        filenameColored = paths.GENERATED_IMAGES_FOLDER + page.name + "_Colored" + cfg.output_format
        if not os.path.isfile(filenameColored) and not dry:
            img = page.renderColored(show=False)
            img.convert("RGB").save(filenameColored, cfg.pil_compression,
                                    optimize=True, quality=cfg.compression_quality)
    except:
        print("We couldn't render " + filenameColored)
                                  


def render_pages_bw(pages, dry=False):
    """
    Takes pages and renders page images in black and white

    :param pages: A list of Page object
    """
    filenames = [(page, dry) for page in pages]
    open_pool(create_page_bw, filenames)
                                  


def render_pages_colored(pages, dry=False):
    """
    Takes pages and renders page images with colors

    :param pages: A list of Page object
    """
    filenames = [(page, dry) for page in pages]
    open_pool(create_page_colored, filenames)