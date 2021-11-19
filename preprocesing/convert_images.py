import os
import cv2
from tqdm import tqdm
from PIL import Image
import concurrent.futures
import numpy as np
import paths
import uuid
from pdf2image import convert_from_path
from io import BytesIO


def convert_single_image(image_path):
    """
    Opens a anime illustration image and turns it black and white
    """
    img = Image.open(image_path)
    bw_img = img.convert("L")
    filename = image_path.split("/")[-1]
    bw_img.save(paths.DATASET_IMAGES_FILES_FOLDER + filename, "JPEG")


def convert_images_to_bw():
    """
    Concurrently and in parallel convert the anime
    illustration images to black and white
    """
    print("Converting images to black and white")
    image_folders = os.listdir(paths.DATASET_IMAGES_DANBOORU_IMAGES_FOLDER)
    for folder in tqdm(image_folders):
        folder_path = paths.DATASET_IMAGES_DANBOORU_IMAGES_FOLDER + folder + "/"
        if os.path.isdir(folder_path):
            image_paths = [folder_path + image
                           for image in os.listdir(folder_path)
                           if image.endswith(".jpg")]

            # Since image processing is CPU and IO intensive
            with concurrent.futures.ProcessPoolExecutor() as executor:
                results = executor.map(convert_single_image, image_paths)


def fill_speech_bubble(img, contours):
    cv2.drawContours(img, contours, -1,
                     (255, 255, 255, 255), cv2.FILLED)
    cv2.drawContours(img, contours, -1, (0, 0, 0, 255), 4)


def create_uuid_image_path():
    return paths.DATASET_IMAGES_SPEECH_BUBBLES_FOLDER + str(uuid.uuid1()) + ".png"


def save_contours(img, multiple=False):
    img_shape = img.shape
    img_grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    contours, _ = cv2.findContours(
        cv2.threshold(img_grey, 100, 255, cv2.THRESH_BINARY)[1],
        cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    empty = np.zeros((img_shape[0], img_shape[1], 4), dtype=np.uint8)

    if not multiple:
        shape = np.copy(empty)
        contours = sorted(contours, reverse=True,
                          key=lambda cnt: cv2.contourArea(cnt))
        first = contours[0]
        x, y, w, h = cv2.boundingRect(first)
        if w * h > 400:
            fill_speech_bubble(shape, [first])
            cv2.imwrite(create_uuid_image_path(), shape)
    else:
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w * h > 400:
                shape = np.copy(empty)
                fill_speech_bubble(shape, [cnt])
                shape = shape[y:y+h, x:x+w]
                cv2.imwrite(create_uuid_image_path(), shape)


def split_speech_bubbles(folder, multiple=False):
    images = os.listdir(folder)
    for i in tqdm(range(len(images))):
        filename = images[i]
        if ".pdf" in filename:
            pages = convert_from_path(folder + filename)
            for page in pages:
                with BytesIO() as f:
                    page.save(f, format="png")
                    f.seek(0)
                    file_bytes = np.asarray(
                        bytearray(f.read()), dtype=np.uint8)
                    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                    save_contours(img, multiple=multiple)
                    break
        else:
            img = cv2.imread(folder + images[i])
            save_contours(img, multiple=multiple)
