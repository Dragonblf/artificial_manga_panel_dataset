
import cv2
import numpy as np
import paths
import os
import json
from tqdm import tqdm


ANNOTATIONS_PANELS_CATEGORY_NAME = "panels"
ANNOTATIONS_PANELS_CATEGORY_INDEX = 1
ANNOTATIONS_SPEECH_BUBBLES_CATEGORY_NAME = "speech_bubbles"
ANNOTATIONS_SPEECH_BUBBLES_CATEGORY_INDEX = 0

# Annotations dict keys
ANNOTATIONS_IMAGE_FILE_NAME = "file_name"
ANNOTATIONS_IMAGE_WIDTH = "width"
ANNOTATIONS_IMAGE_HEIGHT = "height"


def open_json(path):
    with open(path) as f:
        return json.loads(f.read())


def save_json(dict, path):
    with open(path, 'w+') as f:
        json.dump(dict, f)


def contour_to_annotation(contour):
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
            np.squeeze(annotation["segmentation"]).tolist()
        ],
        "area": annotation["area"],
        "bbox": annotation["box"],
        "iscrowd": 0,
        "attributes": {"occluded": False}
    }


def create_coco_annotations_from_segmentations():
    segmented_folder = paths.GENERATED_SEGMENTED_FOLDER
    folders = os.listdir(segmented_folder)

    image_counter = 1
    annotations_counter = 1
    images = []
    annotations = []

    for filename in tqdm(folders):
        folder = segmented_folder + filename
        if os.path.isdir(folder):
            annotations_file = folder + "/" + paths.GENERATED_ANNOTATIONS_FILENAME
            if os.path.exists(annotations_file):
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
                    "file_name": annotation[ANNOTATIONS_IMAGE_FILE_NAME],
                    "license": 0,
                    "flickr_url": "",
                    "coco_url": "",
                    "date_captured": 0
                })
                image_counter += 1

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
            "date_created": "",
            "description": "",
            "url": "https://github.com/seel-channel/artificial_manga_panel_dataset",
            "version": "",
            "year": "2021"
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

    save_json(paths.GENERATED_FOLDER + "coco_" +
              paths.GENERATED_ANNOTATIONS_FILENAME, coco)
