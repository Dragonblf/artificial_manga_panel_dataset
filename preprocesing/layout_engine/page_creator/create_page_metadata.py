import numpy as np
import pyclipper

from ... import config_file as cfg
from ..objects.page import Page
from .create_speech_bubbles_metadata import create_speech_bubbles_metadata
from .create_page_panels_base import create_page_panels_base
from .page_panels_transformers import add_transforms
from ..helpers import get_leaf_panels


def shrink_panels(page):
    """
    A function that uses the pyclipper library]
    to reduce the size of the panel polygon

    :param page: Page whose panels are to be
    shrunk

    :type page: Page

    :return: Page with shrunk panels

    :rtype: Page
    """

    panels = []
    if len(page.leaf_children) < 1:
        get_leaf_panels(page, panels)
        page.leaf_children = panels
    else:
        panels = page.leaf_children

    # For each panel
    for panel in panels:
        # Shrink them
        pco = pyclipper.PyclipperOffset()
        pco.AddPath(panel.get_polygon(),
                    pyclipper.JT_ROUND,
                    pyclipper.ET_CLOSEDPOLYGON)

        shrink_amount = np.random.randint(
            cfg.min_panel_shrink_amount, cfg.max_panel_shrink_amount)
        solution = pco.Execute(shrink_amount)

        # Get the solutions
        changed_coords = []
        if len(solution) > 0:
            for item in solution[0]:
                changed_coords.append(tuple(item))

            changed_coords.append(changed_coords[0])

            # Assign them
            panel.coords = changed_coords
            panel.x1y1 = changed_coords[0]
            panel.x2y2 = changed_coords[1]
            panel.x3y3 = changed_coords[2]
            panel.x4y4 = changed_coords[3]
        else:
            # Assign them as is if there are no solutions
            pass

    return page


def remove_panel(page):
    """
    This function randomly removes
    a panel from pages which have
    more than n+1 panels

    :param page: Page to remove panels from

    :type page: Page

    :return: Page with panels removed

    :rtype: Page
    """

    # If page has > n+1 children so there's
    # at least 1 panel left
    if page.num_panels > cfg.panel_removal_max + 1:

        # Remove 1 to n panels
        remove_number = np.random.choice([1, cfg.panel_removal_max])

        # Remove panel
        for i in range(remove_number):
            page.leaf_children.pop()

    return page


def add_background(page, image_dir, image_dir_path):
    """
    Add a background image to the page

    :param page: Page to add background to

    :type page: Page

    :param image_dir: A list of images

    :type image_dir: list

    :param image_dir_path: path to images used for adding
    the full path to the page

    :type image_dir_path: str

    :return: Page with background

    :rtype: Page
    """

    image_dir_len = len(image_dir)
    idx = np.random.randint(0, image_dir_len)
    page.background = image_dir_path + image_dir[idx]

    return page


def populate_panels(page: Page,
                    image_dir,
                    image_dir_path,
                    font_files,
                    text_dataset,
                    speech_bubble_files,
                    writing_areas,
                    language):
    """
    This function takes all the panels and adds backgorund images
    and speech bubbles to them

    :param page: Page with panels to populate

    :type page: Page

    :param image_dir: List of images to pick from

    :type image_dir: list

    :param image_dir_path: Path of images dir to add to
    panels

    :type image_dir_path: str

    :param font_files: list of font files for speech bubble
    text

    :type font_files: list

    :param text_dataset: A dask dataframe of text to
    pick to render within speech bubble

    :type text_dataset: pandas.dataframe

    :param speech_bubble_files: list of base speech bubble
    template files

    :type speech_bubble_files: list

    :param writing_areas: a list of speech bubble
    writing area tags by filename

    :type writing_areas: list

    :return: Page with populated panels

    :rtype: Page
    """
    speech_bubbles_generated = []

    if page.num_panels > 1:
        for child in page.leaf_children:
            create_speech_bubbles_metadata(child,
                                           image_dir,
                                           image_dir_path,
                                           font_files,
                                           text_dataset,
                                           speech_bubble_files,
                                           writing_areas,
                                           language,
                                           speech_bubbles_generated=speech_bubbles_generated
                                           )
    else:
        create_speech_bubbles_metadata(page,
                                       image_dir,
                                       image_dir_path,
                                       font_files,
                                       text_dataset,
                                       speech_bubble_files,
                                       writing_areas,
                                       language,
                                       speech_bubbles_generated=speech_bubbles_generated
                                       )
    return page


def create_page_metadata(image_dir,
                         image_dir_path,
                         font_files,
                         text_dataset,
                         speech_bubble_files,
                         writing_areas,
                         language
                         ):
    """
    This function creates page metadata for a single page. It includes
    transforms, background addition, random panel removal,
    panel shrinking, and the populating of panels with
    images and speech bubbles.

    :param image_dir: List of images to pick from

    :type image_dir: list

    :param image_dir_path: Path of images dir to add to
    panels

    :type image_dir_path: str

    :param font_files: list of font files for speech bubble
    text

    :type font_files: list

    :param text_dataset: A dask dataframe of text to
    pick to render within speech bubble

    :type text_dataset: pandas.dataframe

    :param speech_bubble_files: list of base speech bubble
    template files

    :type speech_bubble_files: list

    :param writing_areas: a list of speech bubble
    writing area tags by filename

    :type writing_areas: list

    :param language: language used to generate text

    :type language: str

    :return: Created Page with all the bells and whistles

    :rtype: Page
    """

    # Select page type
    page_type = np.random.choice(
        list(cfg.vertical_horizontal_ratios.keys()),
        p=list(cfg.vertical_horizontal_ratios.values())
    )

    # Select number of panels on the page
    # between 1 and 8
    number_of_panels = np.random.choice(
        list(cfg.num_pages_ratios.keys()),
        p=list(cfg.num_pages_ratios.values())
    )

    page = create_page_panels_base(number_of_panels, page_type)

    if np.random.random() < cfg.panel_transform_chance:
        page = add_transforms(page)

    page = shrink_panels(page)
    page = populate_panels(page,
                           image_dir,
                           image_dir_path,
                           font_files,
                           text_dataset,
                           speech_bubble_files,
                           writing_areas,
                           language
                           )

    if np.random.random() < cfg.panel_removal_chance:
        page = remove_panel(page)

    if number_of_panels == 1:
        page = add_background(page, image_dir, image_dir_path)
    else:
        if np.random.random() < cfg.background_add_chance:
            page = add_background(page, image_dir, image_dir_path)

    return page
