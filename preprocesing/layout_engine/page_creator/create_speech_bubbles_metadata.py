import cv2
import numpy as np
import paths

from .. import config_file as cfg
from ..objects.speech_bubble import SpeechBubble


def create_speech_bubbles_metadata(panel,
                                   image_dir,
                                   image_dir_path,
                                   font_files,
                                   text_dataset,
                                   speech_bubble_files,
                                   writing_areas,
                                   language,
                                   speech_bubbles_generated=[],
                                   ):
    """
    This is a helper function that populates a single panel with
    an image, and a set of speech bubbles

    :param panel: Panel to add image and speech bubble to

    :type panel: Panel

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
    """

    # Image to be used inside panel
    select_image_idx = np.random.randint(0, len(image_dir))
    select_image = image_dir[select_image_idx]
    panel.image = image_dir_path + select_image

    # Select number of speech bubbles to assign to panel
    num_speech_bubbles = np.random.randint(cfg.min_speech_bubbles_per_panel,
                                           cfg.max_speech_bubbles_per_panel)

    # Get lengths of datasets
    text_dataset_len = len(text_dataset)
    font_dataset_len = len(font_files)
    speech_bubbles_files = len(speech_bubble_files)

    # Associated speech bubbles
    def create_speech_bubble():
        # Select a font
        font_idx = np.random.randint(0, font_dataset_len)
        font = font_files[font_idx]

        # Select a random language if language is paths.ALL_LANGUAGE
        bubble_language = language
        if language == paths.ALL_LANGUAGE:
            supported = paths.LANGUAGES_SUPPORTED
            bubble_language = supported[np.random.randint(0, len(supported))]

        # Open image and save its dimensions
        speech_bubble_writing_areas = []
        speech_bubble_index = np.random.randint(0, speech_bubbles_files)
        speech_bubble_file = speech_bubble_files[speech_bubble_index]
        img = cv2.imread(speech_bubble_file)
        h, w, _ = img.shape
        padding = cfg.bubble_content_padding
        for area in writing_areas:
            if area["path"] == speech_bubble_file:
                if area["width"] > padding and area["height"] > padding:
                    speech_bubble_writing_areas.append(area)

        if not speech_bubble_writing_areas:
            return

        # Select text for writing areas
        texts = []
        text_indices = []
        for _ in speech_bubble_writing_areas:
            text_idx = np.random.randint(0, text_dataset_len)
            text = text_dataset.iloc[text_idx].to_dict()

            # Transform text (lowercase, uppercase and capitalize)
            text_transform = np.random.randint(0, 5)
            english = text[paths.ENGLISH_LANGUAGE]
            if text_transform in [1, 2]:
                english = english.upper()
            elif text_transform == 3:
                english = english.lower()
            else:
                english = english.capitalize()
            text[paths.ENGLISH_LANGUAGE] = english

            texts.append(text)
            text_indices.append(text_idx)

        # Scale bubble to < 40% of panel area
        bubble_area = h * w
        scale = np.sqrt(
            panel.area * cfg.bubble_to_panel_area_max_ratio / bubble_area)
        w = round(w * scale)
        h = round(h * scale)

        # Select location of bubble in panel
        width_m = np.random.random()
        height_m = np.random.random()

        xy = np.array(panel.coords)
        min_coord = np.min(xy[xy[:, 0] == np.min(xy[:, 0])], 0)

        x = round(min_coord[0] + (panel.width // 2 - 15) * width_m)
        y = round(min_coord[1] + (panel.height // 2 - 15) * height_m)

        # Validate if there is not any speech bubble in the same space or outside page
        def rect_in_rect(r1x, r1y, r1w, r1h, r2x, r2y, r2w, r2h):
            return r1x + r1w >= r2x and r1x <= r2x + r2w and r1y + r1h >= r2y and r1y <= r2y + r2h

        is_able_to_generate = x >= 0 and y >= 0 and x + \
            w <= cfg.page_width and y + h <= cfg.page_height

        if is_able_to_generate:
            for bubble in speech_bubbles_generated:
                width, height = bubble.width, bubble.height
                x1, y1, = bubble.location[0], bubble.location[1]

                if rect_in_rect(x1, y1, width, height, x, y, w, h):
                    is_able_to_generate = False
                    break

        # Create speech bubble
        if is_able_to_generate:
            speech_bubble = SpeechBubble(texts=texts,
                                         text_indices=text_indices,
                                         font=font,
                                         speech_bubble=speech_bubble_file,
                                         writing_areas=speech_bubble_writing_areas,
                                         location=(x, y),
                                         width=w,
                                         height=h,
                                         language=bubble_language)
            speech_bubbles_generated.append(speech_bubble)
            panel.speech_bubbles.append(speech_bubble)
            return speech_bubble

    for _ in range(num_speech_bubbles):
        attempts = 8
        for __ in range(attempts):
            speech_bubble = create_speech_bubble()
            if speech_bubble is not None:
                break
