import concurrent

import cv2
import paths
import numpy as np
from scipy import ndimage

from tqdm import tqdm
from .. import config_file as cfg
from ..convert_images import find_contours
from . import pages_annotator as annotator


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
            pts = []
            for p1 in coordinates:
                p1 = round(p1[0]), round(p1[1])
                if not p1 in pts:
                    pts.append(p1)
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
                elements.append((contours, bubble))
            speech_bubbles += elements

        # Append new elements to lists if it has children
        if panel_children:
            get_panels_and_speech_bubbles(
                panel_children, panels, speech_bubbles)


def create_mask(img, shape, empty, contour, color, filename):
    empty = empty.copy()
    cv2.drawContours(img, [contour], -1, color, 4)
    cv2.drawContours(empty, [contour], -1, (255), cv2.FILLED)
    cv2.drawContours(shape, [contour], -1, (255), cv2.FILLED)
    cv2.imwrite(filename, empty)


def create_segmented_page(name: str):
    """
    This function is used to render a single page from a metadata json file
    to a target location.

    :param name: a str of page.name

    :type name: srt
    """

    output = cfg.output_format
    image_name = name + output
    image_file = paths.GENERATED_IMAGES_FOLDER + image_name
    metadata_file = paths.GENERATED_METADATA_FOLDER + name + cfg.metadata_format

    panels_category = annotator.ANNOTATIONS_PANELS_CATEGORY_NAME
    speech_bubbles_cateogy = annotator.ANNOTATIONS_SPEECH_BUBBLES_CATEGORY_NAME
    folder = paths.GENERATED_SEGMENTED_FOLDER + name + "/"
    panels_masks_folder = folder + panels_category + "/"
    speech_bubble_masks_folder = folder + speech_bubbles_cateogy + "/"

    paths.makeFolders([panels_masks_folder, speech_bubble_masks_folder])

    metadata = annotator.open_json(metadata_file)
    img = cv2.imread(image_file)
    img_shape = img.shape
    empty = np.zeros((img_shape[0], img_shape[1]), np.uint8)
    panels_shape = empty.copy()
    speech_bubbles_shape = empty.copy()

    panels = []
    speech_bubbles = []
    get_panels_and_speech_bubbles(metadata["children"], panels, speech_bubbles)

    annotations = {
        annotator.ANNOTATIONS_IMAGE_WIDTH: img_shape[1],
        annotator.ANNOTATIONS_IMAGE_HEIGHT: img_shape[0],
        annotator.ANNOTATIONS_IMAGE_FILE_NAME: image_file,
        panels_category: [],
        speech_bubbles_cateogy: [],
    }

    for i, contour in enumerate(panels):
        anotation = annotator.contour_to_annotation(contour)
        annotations[panels_category].append(
            anotation)
        create_mask(img, panels_shape, empty, contour,
                    color=(0, 255, 0),
                    filename=panels_masks_folder + str(i) + output)
    for i, speech_bubble in enumerate(speech_bubbles):
        contour, _ = speech_bubble
        anotation = annotator.contour_to_annotation(contour)
        annotations[speech_bubbles_cateogy].append(
            anotation)
        create_mask(img, speech_bubbles_shape, empty, contour,
                    color=(255, 0, 0),
                    filename=speech_bubble_masks_folder + str(i) + output)

    cv2.imwrite(folder + "preview" + output, img)
    cv2.imwrite(folder + panels_category +
                "_mask" + output, panels_shape)
    cv2.imwrite(folder + speech_bubbles_cateogy + "_mask" + output,
                speech_bubbles_shape)

    annotator.save_json(annotations,
                        folder + paths.GENERATED_ANNOTATIONS_FILENAME)


def segment_pages(pages):
    segmented_names = [page.name for page in pages]
    with concurrent.futures.ProcessPoolExecutor() as executor:
        _ = list(tqdm(executor.map(create_segmented_page, segmented_names),
                      total=len(segmented_names)))
