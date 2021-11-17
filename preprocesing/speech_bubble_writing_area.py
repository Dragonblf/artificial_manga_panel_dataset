import cv2
import paths
import os
from tqdm import tqdm


def get_largest_rectangle_inside_contours(img):
    """

    img: cv2.Image

    return: list of ((x1, y1), (x2, y2)) or None
    """
    # Color it in gray
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Create our mask by selecting the non-zero values of the picture
    _, mask = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)

    # Select the contour
    cont, _ = cv2.findContours(
        mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    # if your mask is incurved or if you want better results,
    # you may want to use cv2.CHAIN_APPROX_NONE instead of cv2.CHAIN_APPROX_SIMPLE,
    # but the rectangle search will be longer

    # Get all the points of the contour
    contour = cont[0].reshape(len(cont[0]), 2)

    # Lower steps provide better box fit but it's so slow.
    # Greater steps are faster but a little bit imprecise.
    # I recomend steps beetween [5, 15]
    rects = []
    steps = 6
    countours_range = range(0, len(contour), steps)

    for i in countours_range:
        x1, y1 = contour[i]
        for j in countours_range:
            x2, y2 = contour[j]
            area = abs(y2 - y1) * abs(x2 - x1)
            rects.append(((x1, y1), (x2, y2), area))

    # the first rect of all_rect has the biggest area, so it's the best solution if he fits in the picture
    all_rect = sorted(rects, key=lambda x: x[2], reverse=True)

    # we take the largest rectangle we've got, based on the value of the rectangle area
    # only if the border of the rectangle is not in the black part if the list is not empty
    if all_rect:
        best_rect_found = False
        index_rect = 0
        nb_rect = len(all_rect)

        # we check if the rectangle is  a good solution
        while not best_rect_found and index_rect < nb_rect:
            rect = all_rect[index_rect]
            (x1, y1) = rect[0]
            (x2, y2) = rect[1]

            valid_rect = True

            # we search a black area in the perimeter of the rectangle (vertical borders)
            x = min(x1, x2)
            while x < max(x1, x2) + 1 and valid_rect:
                if mask[y1, x] == 0 or mask[y2, x] == 0:
                    # if we find a black pixel, that means a part of the rectangle is black
                    # so we don't keep this rectangle
                    valid_rect = False
                x += 1

            y = min(y1, y2)
            while y < max(y1, y2) + 1 and valid_rect:
                if mask[y, x1] == 0 or mask[y, x2] == 0:
                    valid_rect = False
                y += 1

            if valid_rect:
                best_rect_found = True
            index_rect += 1

        if best_rect_found:
            return [((x1, y1), (x2, y2))]


def create_speech_bubbles_writing_areas():
    file = paths.DATASET_IMAGES_SPEECH_BUBBLES_WRITING_AREAS_FILE
    folder = paths.DATASET_IMAGES_SPEECH_BUBBLES_FOLDER
    speech_bubbles = os.listdir(folder)
    if os.path.exists(file):
        os.remove(file)
    with open(file, "w+") as f:
        for bubble in tqdm(speech_bubbles):
            if ".png" in bubble:
                file = folder + bubble
                img = cv2.imread(file)
                rects = get_largest_rectangle_inside_contours(img)
                if rects:
                    for pts in rects:
                        p1, p2 = pts
                        x, y = p1
                        items = [file,
                                 str(x), str(y),
                                 str(abs(x - p2[0])), str(abs(y - p2[1]))]
                        f.write(",".join(items) + "\n")
        f.close()
