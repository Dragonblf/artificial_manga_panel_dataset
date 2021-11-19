import os
import concurrent

import cv2
import paths
import json
import numpy as np
from scipy import ndimage

from tqdm import tqdm
from .. import config_file as cfg


def get_panels_and_speech_bubbles(children, panels=[], speech_bubbles=[]):
    def reshape(pts):
        return np.array(pts, np.int32).reshape((-1, 1, 2))

    for panel in children:
        bubbles = panel["speech_bubbles"]
        coordinates = panel["coordinates"]
        panel_children = panel["children"]

        # Convert panel coordinates to cv2's points
        if coordinates and panel["image"] is not None:
            pts = [(round(p1[0]), round(p1[1]))
                   for p1 in coordinates]
            panels += [reshape(pts)]

        # Convert speech bubble coordinates to cv2's points
        if bubbles:
            pts = []
            for bubble in bubbles:
                w, h = bubble["width"], bubble["height"]
                x1, y1 = bubble["location"]
                try:
                    rotation = bubble["transform_metadata"]["rotation_amount"]
                except:
                    rotation = None
                if rotation:
                    # Create a empty rectangle and draw a rectangle
                    image = np.zeros((h, w), np.uint8)
                    cv2.rectangle(image, (0, 0), (w, h), (255), 4)

                    # Rotate image
                    image = ndimage.rotate(image, rotation)

                    # Find contours of rotated rectangle
                    contours, _ = cv2.findContours(
                        cv2.threshold(image, 100, 255, cv2.THRESH_BINARY)[1],
                        cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

                    # Translate rotated rectangle to speech_bubbles's (x1, y1)
                    if contours:
                        new_positions = []
                        for position in contours[0]:
                            x, y = position[0]
                            new_positions.append([[x + x1, y + y1]])
                        pts.append(reshape(new_positions))
                else:
                    x2, y2 = x1 + w, y1 + h
                    new_pts = ((x1, y1), (x2, y1), (x2, y2), (x1, y2))
                    pts.append(reshape(new_pts))
            speech_bubbles += pts

        # Append new elements to lists if it has children
        if panel_children:
            get_panels_and_speech_bubbles(
                panel_children, panels, speech_bubbles)


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
    get_panels_and_speech_bubbles(
        metadata["children"], panels, speech_bubbles, )

    for coordinates in panels:
        cv2.drawContours(img, [coordinates], -1, (0, 255, 0), 4)
    for coordinates in speech_bubbles:
        cv2.drawContours(img, [coordinates], -1, (255, 0, 0), 4)

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
