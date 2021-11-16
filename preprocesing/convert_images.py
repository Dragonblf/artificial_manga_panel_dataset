import os
import cv2
from tqdm import tqdm
from PIL import Image
import concurrent.futures
import numpy as np

image_dataset_dir = "datasets/image_dataset/tagged-anime-illustrations/"\
                    "danbooru-images/danbooru-images/"

processed_image_dir = "datasets/image_dataset/db_illustrations_bw/"


def convert_single_image(image_path):
    """
    Opens a anime illustration image and turns it black and white
    """
    img = Image.open(image_path)
    bw_img = img.convert("L")
    filename = image_path.split("/")[-1]
    bw_img.save(processed_image_dir+filename, "JPEG")


def convert_images_to_bw():
    """
    Concurrently and in parallel convert the anime
    illustration images to black and white
    """
    if not os.path.isdir(processed_image_dir):
        os.mkdir(processed_image_dir)

    print("Converting images to black and white")
    image_folders = os.listdir(image_dataset_dir)
    for folder in tqdm(image_folders):
        folder_path = image_dataset_dir+folder + "/"
        if os.path.isdir(folder_path):
            image_paths = [folder_path + image
                           for image in os.listdir(folder_path)
                           if image.endswith(".jpg")]

            # Since image processing is CPU and IO intensive
            with concurrent.futures.ProcessPoolExecutor() as executor:
                results = executor.map(convert_single_image, image_paths)


def split_speech_bubbles(speech_bubbles_raw_files_path, speech_bubbles_files_path):
    count = 0
    images = os.listdir(speech_bubbles_raw_files_path)
    for i in range(len(images)):
        img = cv2.imread(speech_bubbles_raw_files_path + images[i])
        img_shape = img.shape
        img_grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh_img = cv2.threshold(
            img_grey, 100, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(
            thresh_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        empty = np.zeros((img_shape[0], img_shape[1], 4), dtype=np.uint8)
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w * h > 400:
                count += 1
                shape = np.copy(empty)
                image_name = str(count) + ".png"
                print("Writting image " + image_name)
                cv2.drawContours(shape, [cnt], -1,
                                 (255, 255, 255, 255), cv2.FILLED)
                cv2.drawContours(shape, [cnt], -1, (0, 0, 0, 255), 4)
                shape = shape[y:y+h, x:x+w]
                cv2.imwrite(speech_bubbles_files_path + image_name, shape)