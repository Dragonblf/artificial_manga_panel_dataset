
import cv2
import numpy as np
import paths
import os
import json
from tqdm import tqdm
from .. import config_file as cfg
from ..multiprocessing import POOL_PROCESSES
import multiprocessing as mp


ANNOTATIONS_SPEECH_BUBBLES_CATEGORY_NAME = "speech_bubbles"
ANNOTATIONS_SPEECH_BUBBLES_CATEGORY_INDEX = 1
ANNOTATIONS_PANELS_CATEGORY_NAME = "panels"
ANNOTATIONS_PANELS_CATEGORY_INDEX = 2

# Annotations dict keys
ANNOTATIONS_IMAGE_FILE_NAME = "file_name"
ANNOTATIONS_IMAGE_WIDTH = "width"
ANNOTATIONS_IMAGE_HEIGHT = "height"


def open_json(path: str):
    with open(path) as f:
        return json.loads(f.read())


def save_json(dict: dict, path: str):
    with open(path, 'w+') as f:
        json.dump(dict, f)


def contour_to_annotation(contour: list):
    x, y, w, h = cv2.boundingRect(contour)
    return {
        "segmentation": np.squeeze(contour).tolist(),
        "area": cv2.contourArea(contour),
        "box": [x, y, x + w, y + h],
    }


def contour_annotation_to_coco_annotation(annotation, annotation_id, image_id, category_id):
    return {
        "id": annotation_id,
        "image_id": image_id,
        "category_id": category_id,
        "segmentation": [
            np.array(annotation["segmentation"]).flatten().tolist()
        ],
        "area": annotation["area"],
        "bbox": annotation["box"],
        "iscrowd": 0,
        "attributes": {"occluded": False}
    }


def generate_single_annotations(filename, image_counter, annotations_counter):
    segmented_folder = paths.GENERATED_SEGMENTED_FOLDER
    images, annotations = [], []
    folder = segmented_folder + filename
    if os.path.isdir(folder):
        annotations_file = os.path.join(
            folder, paths.GENERATED_ANNOTATIONS_FILENAME)
        image_file_name = filename + cfg.output_format
        image_file = os.path.join(
            paths.GENERATED_IMAGES_FOLDER, image_file_name)
        if os.path.exists(annotations_file) and os.path.exists(image_file):
            def append_annotation(contours, category_id, annotation_id):
                annotations_counter = annotation_id
                for contour in contours:
                    annotations.append(
                        contour_annotation_to_coco_annotation(
                            contour,
                            image_id=image_counter,
                            annotation_id=annotations_counter,
                            category_id=category_id,
                        ))
                    annotations_counter += 1
                return annotations_counter

            annotation = open_json(annotations_file)
            annotations_counter = append_annotation(
                annotation[ANNOTATIONS_PANELS_CATEGORY_NAME],
                ANNOTATIONS_PANELS_CATEGORY_INDEX,
                annotations_counter)
            annotations_counter = append_annotation(
                annotation[ANNOTATIONS_SPEECH_BUBBLES_CATEGORY_NAME],
                ANNOTATIONS_SPEECH_BUBBLES_CATEGORY_INDEX,
                annotations_counter)
            images.append({
                "id": image_counter,
                "width": annotation[ANNOTATIONS_IMAGE_WIDTH],
                "height": annotation[ANNOTATIONS_IMAGE_HEIGHT],
                "file_name": image_file_name,
                "license": 0,
                "flickr_url": "",
                "coco_url": "",
                "date_captured": 0
            })
            image_counter += 1
    return (images, annotations, image_counter, annotations_counter)


def create_coco_annotations_from_segmentations():
    segmented_folder = paths.GENERATED_SEGMENTED_FOLDER
    folders = os.listdir(segmented_folder)

    image_counter = 1
    annotations_counter = 1
    images = []
    annotations = []

    pool = mp.Pool(processes=POOL_PROCESSES)
    for filename in tqdm(folders):
        data = pool.apply(generate_single_annotations,
                          args=(filename, image_counter, annotations_counter))
        images += data[0]
        annotations += data[1]
        image_counter = data[2]
        annotations_counter = data[3]
    pool.close()

    coco = {
        "licenses": [
            {
                "id": 0,
                "name": "MIT License",
                "url": "https://github.com/seel-channel/artificial_manga_panel_dataset/blob/main/LICENSE"
            }
        ],
        "info": {
            "contributor": "Luis Felipe Murguia Ramos",
            "url": "https://github.com/seel-channel/artificial_manga_panel_dataset",
            "date_created": "",
            "description": "",
            "version": "",
            "year": ""
        },
        "categories": [
            {
                "id": ANNOTATIONS_SPEECH_BUBBLES_CATEGORY_INDEX,
                "name": ANNOTATIONS_SPEECH_BUBBLES_CATEGORY_NAME,
                "supercategory": ""
            },
            {
                "id": ANNOTATIONS_PANELS_CATEGORY_INDEX,
                "name": ANNOTATIONS_PANELS_CATEGORY_NAME,
                "supercategory": ""
            }
        ],
        "images": images,
        "annotations": annotations
    }

    print("Saving COCO annotations...")
    save_json(coco, paths.GENERATED_FOLDER +
              paths.GENERATED_COCO_ANNOTATIONS_FILENAME)

    return coco
