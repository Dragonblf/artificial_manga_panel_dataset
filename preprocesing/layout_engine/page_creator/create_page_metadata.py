import numpy as np
import paths
from .create_speech_bubbles_metadata import create_speech_bubble_metadata
from .create_page_panels_base import create_page_panels_base
from .page_panels_transformers import add_transforms
from .page_panels_shifters import shrink_panels
from ... import config_file as cfg
from ...multiprocessing import open_pool


def create_single_page_metadata(data):
    """
    This function creates page metadata for a single page. It includes
    transforms, background addition, random panel removal,
    panel shrinking, and the populating of panels with
    images and speech bubbles.

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

    :param language: language used to generate text

    :type language: str

    :return: Created Page with all the bells and whistles

    :rtype: Page
    """

    page, panels, background, language = data
    speech_bubbles_generated = []

    for panel in panels:
        child, image, speech_bubbles = panel
        child.image = image
        for speech_bubble in speech_bubbles:
            create_speech_bubble_metadata(child,
                                          speech_bubble,
                                          speech_bubbles_generated,
                                          language)

    # Remove random panels
    if np.random.random() < cfg.panel_removal_chance and page.num_panels > cfg.panel_removal_max + 1:
        remove_number = np.random.choice([1, cfg.panel_removal_max])
        for _ in range(remove_number):
            page.leaf_children.pop()

    page.background = background
    page.dump_data(paths.GENERATED_METADATA_FOLDER, dry=False)
    return page


def create_inital_page_metadata(data):
    images_len, fonts_len, speech_bubbles_len = data
    random = np.random

    # Create page base
    number_of_panels = random.choice(
        list(cfg.num_pages_ratios.keys()),
        p=list(cfg.num_pages_ratios.values())
    )
    page_type = random.choice(
        list(cfg.vertical_horizontal_ratios.keys()),
        p=list(cfg.vertical_horizontal_ratios.values())
    )
    page = create_page_panels_base(number_of_panels, page_type)

    # Get page transforms and effects
    if random.random() < cfg.panel_transform_chance:
        page = add_transforms(page)

    # Select a background_index
    background_index = None
    if random.random() < cfg.background_add_chance:
        background_index = random.randint(0, images_len)

    page = shrink_panels(page)

    panels = []

    # Select panels image and num of speech bubbles
    for panel in page.leaf_children if page.num_panels > 1 else range(1):
        speech_bubbles = []
        image_index = random.randint(0, images_len)
        num_speech_bubbles = random.randint(cfg.min_speech_bubbles_per_panel,
                                            cfg.max_speech_bubbles_per_panel)

        # Select image, font and text of speech bubble
        for __ in range(num_speech_bubbles):
            font_index = random.randint(0, fonts_len)
            speech_bubble_index = np.random.randint(0, speech_bubbles_len)
            speech_bubbles.append((font_index, speech_bubble_index))
        panels.append((panel if page.num_panels > 1 else page,
                      image_index, speech_bubbles))

    return (page, panels, background_index)


def preprocess_metadata(random_indexes,
                        images,
                        fonts,
                        texts,
                        speech_bubbles,
                        no_empty_writing_areas,
                        language):

    texts_len = len(texts)
    texts_iloc = texts.iloc
    preprocessed_metadata = []

    # Select image, fonts and texts from previously generated indexes
    for page, panels, background_index in random_indexes:
        new_panels = []
        for panel, image_index, bubbles in panels:
            new_speech_bubbles = []
            for font_index, speech_bubble_index in bubbles:
                texts, text_indices, writing_areas = [], [], []
                bubble_image = speech_bubbles[speech_bubble_index]
                font = fonts[font_index]
                for area in no_empty_writing_areas[bubble_image]:
                    text_index = np.random.randint(0, texts_len)
                    text_indices.append(text_index)
                    texts.append(texts_iloc[text_index])
                    writing_areas.append(area)
                new_speech_bubbles.append((bubble_image, font, texts,
                                           text_indices, writing_areas))
            new_panels.append((panel, images[image_index], new_speech_bubbles))
        background = images[background_index] if background_index is not None else None
        preprocessed_metadata.append((page, new_panels, background, language))

    return preprocessed_metadata


def create_pages_metadata(n,
                          images,
                          fonts,
                          texts,
                          speech_bubbles,
                          speech_bubbles_writing_areas,
                          language):

    # Validate speech_bubbles without empty area
    padding = cfg.bubble_content_padding
    no_empty_writing_areas = {}
    for area in speech_bubbles_writing_areas:
        if area["width"] > padding and area["height"] > padding:
            path = area["path"]
            if path in no_empty_writing_areas:
                no_empty_writing_areas[path].append(area)
            else:
                no_empty_writing_areas[path] = [area]

    # Set speech_bubble with validated area
    speech_bubbles = list(no_empty_writing_areas.keys())
    speech_bubbles_len = len(speech_bubbles)
    images_len = len(images)
    fonts_len = len(fonts)

    # Get random indexes for images and fonts
    metadata_lens = [(images_len, fonts_len, speech_bubbles_len)
                     for _ in range(n)]
    random_indexes = open_pool(create_inital_page_metadata, metadata_lens)

    preprocessed_metadata = preprocess_metadata(random_indexes, images, fonts, texts,
                                                speech_bubbles, no_empty_writing_areas, language)
    return open_pool(create_single_page_metadata, preprocessed_metadata)
