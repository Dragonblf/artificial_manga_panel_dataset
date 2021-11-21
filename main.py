import pytest
from argparse import ArgumentParser
import pandas as pd
import os
from tqdm import tqdm
import paths

from scraping.download_texts import download_and_extract_jesc
from scraping.download_fonts import get_font_links
from scraping.download_images import download_db_illustrations

from preprocesing.speech_bubble_writing_area import create_speech_bubbles_writing_areas
from preprocesing.text_dataset_format_changer import convert_jesc_to_dataframe
from preprocesing.extract_and_verify_fonts import extract_fonts, move_fonts, verify_font_files
from preprocesing.convert_images import convert_images_to_bw, split_speech_bubbles
from preprocesing.layout_engine.pages_renderer import render_pages
from preprocesing.layout_engine.pages_segmenter import segment_pages
from preprocesing.layout_engine.page_creator.create_page_metadata import create_page_metadata
from preprocesing.layout_engine.pages_annotator import create_coco_annotations_from_segmentations


if __name__ == '__main__':
    usage_message = """
                    This file is designed you to create the AMP dataset
                    To learn more about how to use this open the README.md
                    """

    parser = ArgumentParser(usage=usage_message)

    parser.add_argument("--download_jesc", "-dj",
                        action="store_true",
                        help="Download JESC Japanese/English dialogue corpus")

    parser.add_argument("--download_fonts", "-df",
                        action="store_true",
                        help="Scrape font files")

    parser.add_argument("--download_images", "-di",
                        action="store_true",
                        help="Download anime illustrtations from Kaggle")

    parser.add_argument("--download_speech_bubbles", "-ds",
                        action="store_true",
                        help="Download speech bubbles from Gcloud")

    parser.add_argument("--extract_fonts", "-ef",
                        action="store_true",
                        help="Extract and move fonts from " + paths.DATASET_FONTS_UNZIPPED_FOLDER + " to " + paths.DATASET_FONTS_FILES_FOLDER)

    parser.add_argument("--verify_fonts", "-vf",
                        action="store_true",
                        help="Verify fonts for minimum coverage from")

    parser.add_argument("--convert_images", "-ci",
                        action="store_true",
                        help="Convert downloaded images to black and white")

    parser.add_argument("--split_speech_bubbles", "-ssb",
                        action="store_true",
                        help="Convert downloaded images to black and white")

    parser.add_argument("--calculate_writing_areas", "-cwa",
                        action="store_true",
                        help="Calculate writing areas of speech bubbles")

    parser.add_argument("--make_dirs", "-mk",
                        action="store_true",
                        help="Create all dataset folders")

    parser.add_argument("--language", "-l",
                        help="Text will display inside SpeechBubbles. Available " +
                        str(paths.LANGUAGES_MODE_AVAILABLE),
                        default=paths.ENGLISH_LANGUAGE, type=str)

    parser.add_argument("--generate_pages", "-gp", nargs=1,
                        type=int, help="Generate pages count")

    parser.add_argument("--segmented", "-s",
                        action="store_true", default=False)

    parser.add_argument("--annotations", "-a",
                        action="store_true", default=False)

    parser.add_argument("--dry", action="store_true", default=False)

    parser.add_argument("--run_tests", action="store_true")

    args = parser.parse_args()

    if args.make_dirs:
        paths.makeFolders(paths.DATASET_FOLDER_PATHS)

    # Wrangling with the text dataset
    if args.download_jesc:
        download_and_extract_jesc()
        convert_jesc_to_dataframe()

    # Font dataset
    if args.download_fonts:
        get_font_links()

    # Font verification
    if args.extract_fonts:
        extract_fonts()
        move_fonts()

    if args.verify_fonts:
        verify_font_files()

    if args.calculate_writing_areas:
        create_speech_bubbles_writing_areas(save=args.segmented)

    # Download and convert image from Kaggle
    if args.download_images:
        download_db_illustrations()
        convert_images_to_bw()

    if args.convert_images:
        convert_images_to_bw()

    if args.split_speech_bubbles:
        paths.makeFolders([paths.DATASET_IMAGES_UNSPLITTED_SPEECH_BUBBLES_SINGLE_FOLDER,
                           paths.DATASET_IMAGES_UNSPLITTED_SPEECH_BUBBLES_MULTIPLE_FOLDER,
                           paths.DATASET_IMAGES_SPEECH_BUBBLES_FOLDER])
        print("Splitting single speech bubbles...")
        split_speech_bubbles(
            paths.DATASET_IMAGES_UNSPLITTED_SPEECH_BUBBLES_SINGLE_FOLDER, multiple=False)
        print("Splitting multiple speech bubbles...")
        split_speech_bubbles(
            paths.DATASET_IMAGES_UNSPLITTED_SPEECH_BUBBLES_MULTIPLE_FOLDER, multiple=True)

    # Combines the above in case of small size
    if args.generate_pages is not None:
        language = args.language
        if not language in paths.LANGUAGES_MODE_AVAILABLE:
            raise Exception("That language mode is not avaible. Available " +
                            str(paths.LANGUAGES_MODE_AVAILABLE))

        n = args.generate_pages[0]  # number of pages
        images_folder = paths.DATASET_IMAGES_FILES_FOLDER
        bubbles_folder = paths.DATASET_IMAGES_SPEECH_BUBBLES_FOLDER
        generated_images_folder = paths.GENERATED_IMAGES_FOLDER
        generated_metadata_folder = paths.GENERATED_METADATA_FOLDER

        print("Loading texts in " + language + "...")
        texts_dataset = pd.read_parquet(
            paths.DATASET_TEXT_JESC_DIALOGUES_FOLDER)
        image_dir = os.listdir(images_folder)
        speech_bubble_files = os.listdir(bubbles_folder)
        speech_bubble_files = [bubbles_folder + filename
                               for filename in speech_bubble_files]

        # Load viable fonts for selected language
        print("Loading fonts...")
        viable_font_files = []
        try:
            with open(paths.DATASET_FONTS_VIABLE_FONTS_FILE) as f:
                for line in f.readlines():
                    append_font = False
                    path, japanese_viable, english_viable = line.split(",")
                    english_viable = bool(english_viable.replace("\n", ""))
                    japanese_viable = bool(japanese_viable.replace("\n", ""))
                    if language == paths.ALL_LANGUAGE:
                        append_font = english_viable and japanese_viable
                    elif language == paths.ENGLISH_LANGUAGE:
                        append_font = english_viable
                    elif language == paths.JAPANASE_LANGUAGE:
                        append_font = japanese_viable
                    if append_font:
                        viable_font_files.append(path)
                f.close()
        except:
            pass

        # Load speech bubbles writing areas
        print("Loading writing areas...")
        writing_areas = []
        try:
            with open(paths.DATASET_IMAGES_SPEECH_BUBBLES_WRITING_AREAS_FILE) as f:
                for line in f.readlines():
                    path, x, y, w, h = line.split(",")
                    writing_areas.append({
                        "path": path,
                        "width": int(w),
                        "height": int(h),
                        "x": int(x),
                        "y": int(y),
                    })
                f.close()
        except:
            pass

        print("Creating metadata...")
        pages = []
        paths.makeFolders(paths.GENERATED_FOLDER_PATHS)
        for i in tqdm(range(n)):
            page = create_page_metadata(image_dir,
                                        images_folder,
                                        viable_font_files,
                                        texts_dataset,
                                        speech_bubble_files,
                                        writing_areas,
                                        language)
            page.dump_data(generated_metadata_folder, dry=False)
            pages.append(page)

        print("Rendering images...")
        render_pages(pages, dry=args.dry)
        if args.segmented:
            print("Segmentanting images...")
            segment_pages(pages)

    if args.annotations:
        print("Creating annotations...")
        create_coco_annotations_from_segmentations()

    if args.run_tests:
        pytest.main([
            "tests/unit_tests/",
            "-s",
            "-x",
        ])
