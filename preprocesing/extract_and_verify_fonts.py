import os
import concurrent.futures
import zipfile
import shutil
import dask.dataframe as dd
import itertools
from fontTools.ttLib import TTFont
from fontTools.ttLib import TTLibError
from tqdm import tqdm
from . import config_file as cfg
from pathlib import Path
import paths


def unzip_file(paths):
    """
    Unzip a file
    :param paths: Path to unzip file from and to

    :type paths: list
    """
    with zipfile.ZipFile(paths[0], 'r') as zip_ref:
        zip_ref.extractall(paths[1])


def extract_fonts():
    """
    A function to get the font files which are in zip format and
    extract them
    """
    if not os.path.isdir(paths.DATASET_FONTS_UNZIPPED_FOLDER):
        os.mkdir(paths.DATASET_FONTS_UNZIPPED_FOLDER)

    files = os.listdir(paths.DATASET_FONTS_ZIPPED_FOLDER)
    files = [filename for filename in files if filename.endswith(".zip")]
    filepaths = [(paths.DATASET_FONTS_ZIPPED_FOLDER + filename, paths.DATASET_FONTS_UNZIPPED_FOLDER)
                 for filename in files]

    with concurrent.futures.ProcessPoolExecutor() as executor:
        executor.map(unzip_file, filepaths)


def move_files(paths):
    """
    Wrapper to move files used for parallel execution

    :param paths: A set of paths 0 is from 1 is to

    :type paths: list
    """
    filepath = str(paths[0])
    if not os.path.isfile(filepath):
        shutil.move(filepath, paths[1])


def move_fonts():
    """
    A function to find the .otf and .ttf
    font files from the scraped font files

    :param paths.DATASET_FONTS_UNZIPPED_FOLDER: Path for zip files
    of font files

    :type paths.DATASET_FONTS_UNZIPPED_FOLDER: str

    :param paths.DATASET_FONTS_ZIPPED_FOLDER: Place where all the
    raw font files exist whether zipped or not

    :type paths.DATASET_FONTS_ZIPPED_FOLDER: str

    :param paths.DATASET_FONTS_FILES_FOLDER: Out directory for font files

    :type paths.DATASET_FONTS_FILES_FOLDER: str
    """
    # Get all relevant font files
    print("Finding font files")
    font_files = list(
        Path(paths.DATASET_FONTS_UNZIPPED_FOLDER).rglob("*.[tT][tT][fF]"))
    font_files += list(
        Path(paths.DATASET_FONTS_UNZIPPED_FOLDER).rglob("*.[oO][tT][fF]"))
    font_files += list(Path(paths.DATASET_FONTS_ZIPPED_FOLDER)
                       .rglob("*.[tT][tT][fF]"))
    font_files += list(Path(paths.DATASET_FONTS_ZIPPED_FOLDER)
                       .rglob("*.[oO][tT][fF]"))

    font_files_and_paths = [(font_path, paths.DATASET_FONTS_FILES_FOLDER)
                            for font_path in font_files]

    print("Moving font files")
    for path in font_files_and_paths:
        move_files(path)

    # Clean up the folder
    shutil.rmtree(paths.DATASET_FONTS_UNZIPPED_FOLDER)
    # shutil.rmtree(paths.DATASET_FONTS_ZIPPED_FOLDER)


def make_char_list(row):
    """
    Helper functions to make a set of characters
    from a row in the dataframe of the text corpus

    :param row: A row in the dataframe

    :type param: str

    :return: A set of characters

    :rtype: list
    """
    words = set(row.split())
    all_chars = []
    for word in words:
        chars = [char for char in word]
        all_chars += chars
    return all_chars


def create_japanese_test_characters(render_text_test_file):
    """
    Create a string of the unique characters in the
    japanese text corpus to test whether the fonts being
    used can render enough of the text

    """
    df = dd.read_parquet(paths.DATASET_TEXT_JESC_DIALOGUES_FOLDER)
    print("Loaded DF. Now seperating word to characters")
    char_sep = df['Japanese'].apply(
        make_char_list, meta=("Japanese", "object"))
    char_sep = char_sep.compute()
    print("Char sep done. Starting making lists of characters")
    char_lists = char_sep.aggregate(lambda x: x.tolist())
    print("Made lists. Now aggregating them")
    agg_chars = list(itertools.chain.from_iterable(char_lists))
    print("Aggregation done. Now making a set")
    char_set = list(set(agg_chars))
    japanese_test_characters = " ".join(char_set)
    print("Writing file")
    with open(render_text_test_file, "w+", encoding="utf-8") as wf:
        wf.write(japanese_test_characters)


def contains_char(font, glyph):
    """
    Check if a font file has the character
    glyph specified

    :param font: A TTFont object from fontTools

    :type font: TTFont

    :param glyph: A character glyph

    :type glyph: str

    :return: 0 = False. 1 = False

    :rtype: int
    """
    for table in font['cmap'].tables:
        if ord(glyph) in table.cmap.keys():
            return 1
    return 0


def verify_font_files():
    """
    A function that tests whether the font files
    that have been scraped meet the benchmark of
    rendering at least x% (as specififed in the config)
    of the unique characters in the text corpus
    """
    if not os.path.isfile(paths.DATASET_FONTS_RENDER_TEST_FILE):
        print("Character test string does exist. Generating!")
        create_japanese_test_characters(paths.DATASET_FONTS_RENDER_TEST_FILE)

    # File to create a test string of unique chars in the corpus
    japanese_test_characters = ""
    english_test_characters = "AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz"
    # spanish_test_characters = english_test_characters + "ÁáÉéÍíÓóÚú"
    with open(paths.DATASET_FONTS_RENDER_TEST_FILE, "r", encoding="utf-8") as test_file:
        japanese_test_characters = test_file.readlines()[0]
    all_fonts = os.listdir(paths.DATASET_FONTS_FILES_FOLDER)

    english_chars = list(english_test_characters)
    japanese_chars = japanese_test_characters.split(" ")
    japanese_total_chars = len(japanese_chars)
    english_total_chars = len(english_chars)

    fonts_coverage = []
    print("Verifying fonts")
    for font_name in tqdm(all_fonts):
        if font_name == ".DS_Store":
            continue
        font_path = paths.DATASET_FONTS_FILES_FOLDER + font_name
        try:
            font = TTFont(font_path)
        except TTLibError as e:
            print(font_path)

        english_char_count = 0
        japanese_char_count = 0
        for char in japanese_chars:
            japanese_char_count += contains_char(font, char)
        for char in english_chars:
            english_char_count += contains_char(font, char)

        japanese_coverage = japanese_char_count / japanese_total_chars
        english_coverage = english_char_count / english_total_chars
        fonts_coverage.append([font_path, japanese_coverage, english_coverage])

    print("Writing viability to file: ", paths.DATASET_FONTS_VIABLE_FONTS_FILE)
    with open(paths.DATASET_FONTS_VIABLE_FONTS_FILE, "w+") as viable_font_file:
        for font in fonts_coverage:
            print(font[1:])
            coverage_states = []
            for coverage in font[1:]:
                coverage_states.append(
                    str(coverage > cfg.font_character_coverage))
            viable_font_file.write(
                font[0] + "," + ",".join(coverage_states) + "\n")
