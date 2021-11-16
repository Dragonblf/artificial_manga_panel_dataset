import pytest
from argparse import ArgumentParser
import pandas as pd
import os
from tqdm import tqdm
import paths
from scraping.download_texts import download_and_extract_jesc
from scraping.download_fonts import get_font_links
from scraping.download_images import download_db_illustrations

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
        # render_text_test_file = paths.DATASET_FONTS_FOLDER + "render_test_text.txt"
        # verify_font_files(
        #     paths.DATASET_TEXT_JESC_DIALOGUES_FOLDER,
        #     render_text_test_file,
        #     paths.DATASET_FONTS_FILES_FOLDER,
        #     paths.DATASET_FONTS_FOLDER
        # )

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
        image_dir = os.listdir(paths.DATASET_IMAGES_FILES_FOLDER)
        text_dataset = pd.read_parquet(
            paths.DATASET_TEXT_JESC_DIALOGUES_FOLDER)

        speech_bubble_files = os.listdir(
            paths.DATASET_IMAGES_SPEECH_BUBBLES_FOLDER)
        speech_bubble_files = [paths.DATASET_IMAGES_SPEECH_BUBBLES_FOLDER + filename
                               for filename in speech_bubble_files
                               ]
        paths.makeFolders(paths.GENERATED_FOLDER_PATHS)
        viable_font_files = []
        with open(paths.DATASET_FONTS_VIABLE_FONTS_FILE) as viable_fonts:
            for line in viable_fonts.readlines():
                path, viable = line.split(",")
                viable = viable.replace("\n", "")
                if viable == "True":
                    viable_font_files.append(path)

        print("Running creation of metadata")
        pages = []
        for i in tqdm(range(n)):
            page = create_page_metadata(image_dir,
                                        paths.DATASET_IMAGES_FILES_FOLDER,
                                        viable_font_files,
                                        text_dataset,
                                        speech_bubble_files)
            page.dump_data(paths.GENERATED_METADATA_FOLDER, dry=False)
            pages.append(page)

        if not os.path.isdir(paths.GENERATED_METADATA_FOLDER):
            print("There is no metadata please generate metadata first")
            if not args.dry:
                os.mkdir(paths.GENERATED_IMAGES_FOLDER)
        else:
            print("Loading metadata and rendering")
            render_pages(pages, paths.GENERATED_IMAGES_FOLDER, dry=args.dry)

    if args.run_tests:
        pytest.main([
            "tests/unit_tests/",
            "-s",
            "-x",
        ])
