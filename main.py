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
from preprocesing.layout_engine.page_creator import render_pages
from preprocesing.layout_engine.page_dataset_creator import (
    create_page_metadata
)
from tqdm import tqdm
import os
import pandas as pd
from argparse import ArgumentParser
import pytest
from PIL import features

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
                        help="Extract and move fonts from datasets/font_dataset/font_file_raw_downloads/ to datasets/font_dataset/font_files")

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

    metadata_folder = "datasets/page_metadata/"
    images_folder = "datasets/page_images/"
    images_path = "datasets/image_dataset/"
    font_dataset_path = "datasets/font_dataset/"
    text_dataset_path = "datasets/text_dataset/"
    fonts_raw_dir = font_dataset_path + "font_file_raw_downloads/"
    fonts_zip_output = font_dataset_path + "fonts_zip_output/"
    font_file_dir = font_dataset_path + "font_files/"
    dataframe_file = text_dataset_path + "jesc_dialogues"
    metadata_folder = "datasets/page_metadata/"
    image_dir_path = images_path + "db_illustrations_bw/"
    speech_bubbles_path = "datasets/speech_bubbles_dataset/"
    speech_bubbles_raw_files_path = speech_bubbles_path + "raw_files/"
    speech_bubbles_files_path = speech_bubbles_path + "files/"
    tagged_images_path = images_path + "tagged-anime-illustrations/"
    danbooru_images_path = tagged_images_path + "danbooru-images/danbooru-images/"

    if args.make_dirs:
        paths = [metadata_folder,
                 images_folder,
                 images_path,
                 font_dataset_path,
                 text_dataset_path,
                 fonts_raw_dir,
                 fonts_zip_output,
                 font_file_dir,
                 dataframe_file,
                 metadata_folder,
                 image_dir_path,
                 speech_bubbles_path,
                 speech_bubbles_raw_files_path,
                 speech_bubbles_files_path,
                 tagged_images_path,
                 danbooru_images_path]

        for path in paths:
            if not os.path.exists(path):
                os.makedirs(path)

    # Wrangling with the text dataset
    if args.download_jesc:
        download_and_extract_jesc()
        convert_jesc_to_dataframe()

    # Font dataset
    if args.download_fonts:
        get_font_links()

    # Font verification
    if args.extract_fonts:
        extract_fonts(fonts_zip_output, fonts_raw_dir)
        move_fonts(fonts_zip_output, fonts_raw_dir, font_file_dir)

    if args.verify_fonts:
        render_text_test_file = font_dataset_path + "render_test_text.txt"
        verify_font_files(
            dataframe_file,
            render_text_test_file,
            font_file_dir,
            font_dataset_path
        )

    # Download and convert image from Kaggle
    if args.download_images:
        download_db_illustrations()
        convert_images_to_bw()

    if args.convert_images:
        convert_images_to_bw()

    if args.split_speech_bubbles:
        split_speech_bubbles(speech_bubbles_raw_files_path,
                             speech_bubbles_files_path)

    # Combines the above in case of small size
    if args.generate_pages is not None:
        # if not features.check('raqm'):
        #     raise Exception(
        #         "Libraqm is required for rendering CJK text properly. Follow instructions https://github.com/HOST-Oman/libraqm")

        n = args.generate_pages[0]  # number of pages

        print("Loading files")
        image_dir = os.listdir(image_dir_path)
        text_dataset = pd.read_parquet(text_dataset_path + "jesc_dialogues")

        speech_bubble_files = os.listdir(speech_bubbles_files_path)
        speech_bubble_files = [speech_bubbles_files_path + filename
                               for filename in speech_bubble_files
                               ]

        # speech_bubble_tags = pd.read_csv(speech_bubbles_path +
        #                                  "writing_area_labels.csv")
        viable_font_files = []
        with open(font_dataset_path + "viable_fonts.csv") as viable_fonts:
            for line in viable_fonts.readlines():
                path, viable = line.split(",")
                viable = viable.replace("\n", "")
                if viable == "True":
                    viable_font_files.append(path)

        print("Running creation of metadata")
        for i in tqdm(range(n)):
            page = create_page_metadata(image_dir,
                                        image_dir_path,
                                        viable_font_files,
                                        text_dataset,
                                        speech_bubble_files,
                                        # speech_bubble_tags
                                        )
            page.dump_data(metadata_folder, dry=False)

        if not os.path.isdir(metadata_folder):
            print("There is no metadata please generate metadata first")
        else:
            if not os.path.isdir(images_folder) and not args.dry:
                os.mkdir(images_folder)

            print("Loading metadata and rendering")
            render_pages(metadata_folder, images_folder, dry=args.dry)

    if args.run_tests:
        pytest.main([
            "tests/unit_tests/",
            "-s",
            "-x",
        ])
