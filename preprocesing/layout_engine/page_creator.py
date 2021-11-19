import os
import concurrent

import cv2
import paths
import json
import numpy as np
from scipy import ndimage

from tqdm import tqdm
from .. import config_file as cfg
from ..convert_images import find_contours


def move_contours(contours, xy: list):
    new_contours = []
    for points in contours:
        x1, y1 = xy
        new_points = []
        for position in points:
            x, y = position[0]
            new_points.append([[x + x1, y + y1]])
        new_contours.append(reshape_points(new_points))
    return new_contours


def reshape_points(pts):
    return np.array(pts, np.int32).reshape((-1, 1, 2))


def get_panels_and_speech_bubbles(children, panels=[], speech_bubbles=[]):
    for panel in children:
        bubbles = panel["speech_bubbles"]
        coordinates = panel["coordinates"]
        panel_children = panel["children"]

        # Convert panel coordinates to cv2's points
        if coordinates and panel["image"] is not None:
            pts = [(round(p1[0]), round(p1[1]))
                   for p1 in coordinates]
            panels += [reshape_points(pts)]

        # Convert speech bubble coordinates to cv2's points
        if bubbles:
            elements = []
            for bubble in bubbles:
                w, h = int(bubble["width"]), int(bubble["height"])
                x1, y1 = bubble["location"]

                # Read image
                image = cv2.imread(
                    bubble["speech_bubble"], cv2.IMREAD_GRAYSCALE)
                image = cv2.resize(image, (w, h))

                # Rotate image
                try:
                    rotation = bubble["transform_metadata"]["rotation_amount"]
                    image = ndimage.rotate(image, rotation)
                except:
                    pass

                # Find contours of rotated rectangle
                contours = find_contours(image)
                contours = sorted(contours, reverse=True,
                                  key=lambda cnt: cv2.contourArea(cnt))

                # Translate rotated rectangle to speech_bubbles's (x1, y1)
                contours = move_contours([contours[0]], (x1, y1))[0]
                elements.append(contours)
            speech_bubbles += elements

        # Append new elements to lists if it has children
        if panel_children:
            get_panels_and_speech_bubbles(
                panel_children, panels, speech_bubbles)


def create_mask(img, shape, contour, color, filename):
    shape = shape.copy()
    cv2.drawContours(img, [contour], -1, color, 4)
    cv2.drawContours(shape, [contour], -1, (255), cv2.FILLED)
    cv2.imwrite(filename, shape)


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

    image_segmented_folder = paths.GENERATED_SEGMENTED_FOLDER + name + "/"
    panels_masks = image_segmented_folder + "panels/"
    speech_bubble_masks = image_segmented_folder + "speech_bubbles/"
    segmented_file = image_segmented_folder + image_name

    paths.makeFolders([panels_masks, speech_bubble_masks])

    metadata = data
    if metadata is None:
        with open(metadata_file) as f:
            metadata = json.loads(f.read())
    img = cv2.imread(image_file)
    img_shape = img.shape
    empty = np.zeros((img_shape[0], img_shape[1]), np.uint8)

    panels = []
    speech_bubbles = []
    get_panels_and_speech_bubbles(metadata["children"], panels, speech_bubbles)

    for i, contour in enumerate(panels):
        create_mask(img, empty, contour,
                    color=(0, 255, 0),
                    filename=panels_masks + str(i) + cfg.output_format)
    for i, contour in enumerate(speech_bubbles):
        create_mask(img, empty, contour,
                    color=(255, 0, 0),
                    filename=speech_bubble_masks + str(i) + cfg.output_format)

    cv2.imwrite(segmented_file, img)
    # cv2.imwrite(paths.GENERATED_SEGMENTED_FOLDER + image_name, img)


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
