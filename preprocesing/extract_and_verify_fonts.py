import os
import concurrent.futures
import dask.dataframe as dd
import itertools
from fontTools.ttLib import TTFont, TTLibError
from tqdm import tqdm
from . import config_file as cfg
from .zip_compressor import unzip_file
from pathlib import Path
import paths
from .multiprocessing import open_pool


def extract_fonts():
    """
    A function to get the font files which are in zip format and
    extract them
    """
    print("Extracting fonts...")
    unzipped = paths.DATASET_FONTS_UNZIPPED_FOLDER
    paths.makeFolders([unzipped])
    files = os.listdir(paths.DATASET_FONTS_ZIPPED_FOLDER)
    files = [filename for filename in files if filename.endswith(".zip")]
    filepaths = [(paths.DATASET_FONTS_ZIPPED_FOLDER + filename, unzipped)
                 for filename in files]

    open_pool(lambda path: unzip_file(path[0], path[1]), filepaths)


def move_files(paths):
    """
    Wrapper to move files used for parallel execution

    :param paths: A set of paths 0 is from 1 is to

    :type list: (Path, str)
    """
    destination = str(paths[1])
    if not os.path.exists(destination):
        paths[0].rename(destination)


def move_fonts():
    """
    A function to find the .otf and .ttf
    font files from the scraped font files
    """
    # Get all relevant font files
    fonts = paths.DATASET_FONTS_FILES_FOLDER
    zipped = paths.DATASET_FONTS_ZIPPED_FOLDER
    unzipped = paths.DATASET_FONTS_UNZIPPED_FOLDER

    print("Finding fonts [.otf, .ttf]...")
    font_files = list(Path(unzipped).rglob("*.[tT][tT][fF]"))
    font_files += list(Path(unzipped).rglob("*.[oO][tT][fF]"))
    font_files += list(Path(zipped).rglob("*.[tT][tT][fF]"))
    font_files += list(Path(zipped).rglob("*.[oO][tT][fF]"))

    font_files_and_paths = [(font_path, fonts + font_path.name)
                            for font_path in font_files]

    print("Moving fonts...")
    open_pool(move_files, font_files_and_paths)

    # Clean up the folder
    # print("Deleting unzipped and zipped folders...")
    # shutil.rmtree(unzipped)
    # shutil.rmtree(zipped)


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
    char_sep = df[paths.JAPANASE_LANGUAGE].apply(
        make_char_list, meta=(paths.JAPANASE_LANGUAGE, "object"))
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
        # Ignore files start with a dot
        if font_name[0] == ".":
            continue
        font_path = paths.DATASET_FONTS_FILES_FOLDER + font_name
        try:
            font = TTFont(font_path)
            english_char_count = 0
            japanese_char_count = 0
            for char in japanese_chars:
                japanese_char_count += contains_char(font, char)
            for char in english_chars:
                english_char_count += contains_char(font, char)
            japanese_coverage = japanese_char_count / japanese_total_chars
            english_coverage = english_char_count / english_total_chars
            fonts_coverage.append(
                [font_path, japanese_coverage, english_coverage])
        except TTLibError as e:
            print("ERROR in" + font_path + ": " + e)

    print("Writing viability to file: ", paths.DATASET_FONTS_VIABLE_FONTS_FILE)
    with open(paths.DATASET_FONTS_VIABLE_FONTS_FILE, "w+") as viable_font_file:
        for font in fonts_coverage:
            coverage_states = []
            for coverage in font[1:]:
                coverage_states.append(
                    str(coverage > cfg.font_character_coverage))
            viable_font_file.write(
                font[0] + "," + ",".join(coverage_states) + "\n")
