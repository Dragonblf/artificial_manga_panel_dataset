import os
import concurrent

import cv2
import paths
import json

from tqdm import tqdm
from .objects.page import Page
from .. import config_file as cfg


def get_panels_and_speech_bubbles(children, panels=[], speech_bubbles=[]):
    for panel in children:
        bubbles = panel["speech_bubbles"]
        coordinates = panel["coordinates"]
        panel_children = panel["children"]
        if coordinates:
            panels += [coordinates]
        if bubbles:
            speech_bubbles += bubbles
        if panel_children:
            get_panels_and_speech_bubbles(
                panel_children, panels,
                speech_bubbles)


def create_segmented_page(name: str, data=None):
    """
    This function is used to render a single page from a metadata json file
    to a target location.

    :param name: a str of page.name

    :type name: srt
    """
    image_name = name + cfg.output_format
    image_file = paths.GENERATED_IMAGES_FOLDER + image_name
    metadata_file = paths.GENERATED_METADATA_FOLDER + name + cfg.metadata_format
    segmented_file = paths.GENERATED_SEGMENTED_FOLDER + image_name

    metadata = data
    if metadata is None:
        with open(metadata_file) as f:
            metadata = json.loads(f.read())
    img = cv2.imread(image_file)

    panels = []
    speech_bubbles = []
    get_panels_and_speech_bubbles(metadata["children"], panels, speech_bubbles)

    for coordinates in panels:
        for i in range(1, len(coordinates)):
            p1, p2 = coordinates[i - 1], coordinates[i]
            p1 = (round(p1[0]), round(p1[1]))
            p2 = (round(p2[0]), round(p2[1]))
            cv2.line(img, p1, p2, (0, 255, 0), 4)
    for bubble in speech_bubbles:
        # TODO: Apply rotation
        x, y = bubble["location"]
        cv2.rectangle(img, (x, y),
                      (x + bubble["width"], y + bubble["height"]),
                      (255, 0, 0), 4)

    cv2.imwrite(segmented_file, img)


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


def segment_pages(pages):
    segmented_names = [page.name for page in pages]
    with concurrent.futures.ProcessPoolExecutor() as executor:
        _ = list(tqdm(executor.map(create_segmented_page, segmented_names),
                      total=len(segmented_names)))
