import cv2
import numpy as np
import paths

from ... import config_file as cfg
from ..objects.speech_bubble import SpeechBubble

MAX_ATTEMPS = 5


def create_speech_bubble_metadata(panel,
                                  speech_bubble,
                                  speech_bubbles_generated,
                                  language,
                                  attempt=0):
    image, font, texts, text_indices, speech_bubble_writing_areas = speech_bubble

    # Select a random language if language is paths.ALL_LANGUAGE
    bubble_language = language
    if language == paths.ALL_LANGUAGE:
        supported = paths.LANGUAGES_SUPPORTED
        bubble_language = supported[np.random.randint(0, len(supported))]

    # Open image and save its dimensions
    img = cv2.imread(image)
    h, w, _ = img.shape

    if not speech_bubble_writing_areas:
        return

    # Select text for writing areas
    texts_dict = []
    for i in range(len(speech_bubble_writing_areas)):
        # Transform text (lowercase, uppercase and capitalize)
        text_transform = np.random.randint(0, 5)
        text = texts[i].to_dict()
        english = text[paths.ENGLISH_LANGUAGE]
        if text_transform in [1, 2]:
            english = english.upper()
        elif text_transform == 3:
            english = english.lower()
        else:
            english = english.capitalize()
        text[paths.ENGLISH_LANGUAGE] = english
        texts_dict.append(text)

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
        speech_bubble = SpeechBubble(texts=texts_dict,
                                     text_indices=text_indices,
                                     font=font,
                                     speech_bubble=image,
                                     writing_areas=speech_bubble_writing_areas,
                                     location=(x, y),
                                     width=w,
                                     height=h,
                                     language=bubble_language)
        speech_bubbles_generated.append(speech_bubble)
        panel.speech_bubbles.append(speech_bubble)
    elif attempt < MAX_ATTEMPS:
        create_speech_bubble_metadata(panel,
                                      speech_bubble,
                                      speech_bubbles_generated,
                                      language, attempt=attempt + 1)
