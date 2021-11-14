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


def unzip_file(paths):
    """
    Unzip a file
    :param paths: Path to unzip file from and to

    :type paths: list
    """
    with zipfile.ZipFile(paths[0], 'r') as zip_ref:
        zip_ref.extractall(paths[1])


def extract_fonts(fonts_zip_output, fonts_raw_dir):
    """
    A function to get the font files which are in zip format and
    extract them
    """
    if not os.path.isdir(fonts_zip_output):
        os.mkdir(fonts_zip_output)

    files = os.listdir(fonts_raw_dir)
    files = [filename for filename in files if filename.endswith(".zip")]
    filepaths = [(fonts_raw_dir + filename, fonts_zip_output)
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


def move_fonts(fonts_zip_output, fonts_raw_dir, font_file_dir):
    """
    A function to find the .otf and .ttf
    font files from the scraped font files

    :param fonts_zip_output: Path for zip files
    of font files

    :type fonts_zip_output: str

    :param fonts_raw_dir: Place where all the
    raw font files exist whether zipped or not

    :type fonts_raw_dir: str

    :param font_file_dir: Out directory for font files

    :type font_file_dir: str
    """
    # Get all relevant font files
    print("Finding font files")
    font_files = list(Path(fonts_zip_output).rglob("*.[tT][tT][fF]"))
    font_files += list(Path(fonts_zip_output).rglob("*.[oO][tT][fF]"))
    font_files += list(Path(fonts_raw_dir).rglob("*.[tT][tT][fF]"))
    font_files += list(Path(fonts_raw_dir).rglob("*.[oO][tT][fF]"))

    font_files_and_paths = [(font_path, font_file_dir)
                            for font_path in font_files]

    print("Moving font files")
    for path in font_files_and_paths:
        move_files(path)

    # Clean up the folder
    shutil.rmtree(fonts_zip_output)
    shutil.rmtree(fonts_raw_dir)


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


def create_character_test_string(dataframe_file, render_text_test_file):
    """
    Create a string of the unique characters in the
    japanese text corpus to test whether the fonts being
    used can render enough of the text

    """
    df = dd.read_parquet(dataframe_file)
    print("Loaded DF. Now seperating word to characters")
    char_sep = df['Japanese'].apply(make_char_list, meta=("Japanese",
                                                          "object"
                                                          )
                                    )
    char_sep = char_sep.compute()
    print("Char sep done. Starting making lists of characters")
    char_lists = char_sep.aggregate(lambda x: x.tolist())
    print("Made lists. Now aggregating them")
    agg_chars = list(itertools.chain.from_iterable(char_lists))
    print("Aggregation done. Now making a set")
    char_set = list(set(agg_chars))
    test_string = " ".join(char_set)
    print("Writing file")
    with open(render_text_test_file, "w+", encoding="utf-8") as wf:
        wf.write(test_string)


def has_glyph(font, glyph):
    """
    Check if a font file has the character
    glyph specified

    :param font: A TTFont object from fontTools

    :type font: TTFont

    :param glyph: A character glyph

    :type glyph: str

    :return: 0 or 1 as a yes or no

    :rtype: int
    """
    for table in font['cmap'].tables:
        if ord(glyph) in table.cmap.keys():
            return 1
    return 0


def verify_font_files(dataframe_file,
                      render_text_test_file,
                      font_file_dir,
                      font_dataset_path
                      ):
    """
    A function that tests whether the font files
    that have been scraped meet the benchmark of
    rendering at least x% (as specififed in the config)
    of the unique characters in the text corpus
    """
    if not os.path.isfile(render_text_test_file):
        print("Character test string does exist. Generating!")
        create_character_test_string(dataframe_file, render_text_test_file)

    # File to create a test string of unique chars in the
    # corpus
    test_string = ""
    with open(render_text_test_file, "r", encoding="utf-8") as test_file:
        test_string = test_file.readlines()[0]

    chars = test_string.split(" ")
    all_fonts = os.listdir(font_file_dir)

    total_chars = len(chars)

    coverages = []
    print("Verifying fonts")
    for font_name in tqdm(all_fonts):
        if font_name == ".DS_Store":
            continue
        font_path = font_file_dir + font_name
        try:
            font = TTFont(font_path)
        except TTLibError as e:
            print(font_path)

        has_glyph_list = []
        for char in chars:
            has_glyph_list.append(has_glyph(font, char))

        coverage = sum(has_glyph_list)/total_chars
        coverages.append([font_path, coverage])

    print("Writing viability to file:", font_dataset_path+"viable_fonts.csv")
    with open(font_dataset_path+"viable_fonts.csv", "w+") as viable_font_file:
        for font in coverages:
            # Coverge %
            if font[1] > cfg.font_character_coverage:
                viable = True
            else:
                viable = False
            viable_font_file.write(font[0] + ","+str(viable)+"\n")
