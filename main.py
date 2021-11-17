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
from preprocesing.extract_and_verify_fonts import (
    extract_fonts,
    move_fonts,
    verify_font_files
)
from preprocesing.convert_images import convert_images_to_bw, split_speech_bubbles
from preprocesing.layout_engine.page_creator import render_pages, render_pages_from_files
from preprocesing.layout_engine.page_dataset_creator import create_page_metadata


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
                        help="Create all dataset folders")

    parser.add_argument("--make_dirs", "-mk",
                        action="store_true",
                        help="Create all dataset folders")

    parser.add_argument("--render_pages", "-rp", action="store_true")
    parser.add_argument("--generate_pages", "-gp", nargs=1, type=int)
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
        create_speech_bubbles_writing_areas()

    # Download and convert image from Kaggle
    if args.download_images:
        download_db_illustrations()
        convert_images_to_bw()

    if args.convert_images:
        convert_images_to_bw()

    if args.split_speech_bubbles:
        split_speech_bubbles()

    # Combines the above in case of small size
    if args.generate_pages is not None:
        # if not features.check('raqm'):
        #     raise Exception(
        #         "Libraqm is required for rendering CJK text properly. Follow instructions https://github.com/HOST-Oman/libraqm")

        n = args.generate_pages[0]  # number of pages

        print("Loading files")
        images_folder = paths.DATASET_IMAGES_FILES_FOLDER
        bubbles_folder = paths.DATASET_IMAGES_SPEECH_BUBBLES_FOLDER
        generated_images_folder = paths.GENERATED_IMAGES_FOLDER
        generated_metadata_folder = paths.GENERATED_METADATA_FOLDER

        texts_dataset = pd.read_parquet(
            paths.DATASET_TEXT_JESC_DIALOGUES_FOLDER)
        image_dir = os.listdir(images_folder)
        speech_bubble_files = os.listdir(bubbles_folder)
        speech_bubble_files = [bubbles_folder + filename
                               for filename in speech_bubble_files]

        # Load viable fonts for selected language
        viable_font_files = []
        try:
            with open(paths.DATASET_FONTS_VIABLE_FONTS_FILE) as f:
                for line in f.readlines():
                    path, japanese_viable, english_viable = line.split(",")
                    japanese_viable = japanese_viable.replace("\n", "")
                    english_viable = english_viable.replace("\n", "")
                    if japanese_viable == "True":
                        viable_font_files.append(path)
                f.close()
        except:
            pass

        # Load speech bubbles writing areas
        writing_areas = []
        try:
            with open(paths.DATASET_IMAGES_SPEECH_BUBBLES_WRITING_AREAS_FILE) as f:
                for line in f.readlines():
                    path, x, y, w, h = line.split(",")
                    writing_areas.append({
                        "path": path,
                        "x": int(x),
                        "y": int(y),
                        "width": int(w),
                        "height": int(h),
                    })
                f.close()
        except:
            pass

        print("Running creation of metadata")
        pages = []
        paths.makeFolders(paths.GENERATED_FOLDER_PATHS)
        for i in tqdm(range(n)):
            page = create_page_metadata(image_dir,
                                        images_folder,
                                        viable_font_files,
                                        texts_dataset,
                                        speech_bubble_files,
                                        writing_areas)
            page.dump_data(generated_metadata_folder, dry=False)
            pages.append(page)

        if not os.path.isdir(generated_metadata_folder):
            print("There is no metadata please generate metadata first")
            if not args.dry:
                os.mkdir(generated_images_folder)
        else:
            print("Loading metadata and rendering")
            render_pages(pages, generated_images_folder, dry=args.dry)

    if args.run_tests:
        pytest.main([
            "tests/unit_tests/",
            "-s",
            "-x",
        ])
