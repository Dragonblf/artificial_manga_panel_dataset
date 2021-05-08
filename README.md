# Artifical Manga Panel Dataset - AMP-D
I love manga, but can't read Japanese. So I decided to build something that'll help me translate the manga into 
English. Sadly I couldn't find a dataset to train my speech bubble detector on so I made this.

## What is in this repo?
This repository contains the associated files and links to create an artificial manga panel dataset.
Here's a sample of an image created with this code:
![Sample image](docs/misc_files/sample.png | width=425)

## Setup and usage
If you just want to use the dataset and not change anything you can find it at <put link to kaggle here>

If you'd like to change the way the creator works, make your own files or contribute to the project pleae follow these instructions

1. Libraqm is required for rendering CJK text properly. Follow instructions [here](https://github.com/HOST-Oman/libraqm)
2. ```pip3 install -r requirements.txt``
3. You can get the base materials for the dataset by [emailing me](mailto:aasimsani05@gmail.com) for the key and then running:
  ```
  export GOOGLE_APPLICATION_CREDENTIALS=config/ampd_key.json
  dvc pull
  ```
4. In case you want to modify individual scripts for scraping or cleaning this downloaded data you can find them in ```main.py```
5. Before you start just run ```python3 main.py --run_tests``` to make sure
you have all the libraries installed and things are working fine
6. Now you can run ```python3 main.py --generate_pages N``` to make pages
7. You can modify ```preprocessing/config_file.py``` to change how the generator works

## Current progress:

Steps:
- [x] Find relevant japanese dialogue dataset
- [x] Find manga like japanese fonts
- [x] Find different text bubble types
- [x] Find manga images or other black and white images to use to fill panels
- [x] Create a few manga page layout templates
- [x] Create manga panels by combining the above elements
- [x] Create font transformations
- [x] Replace layout templates with manga panel generator
- [ ] Upload dataset to Kaggle

### Data variety
- 196 fonts with >80% character coverage
- 91 unique speech bubble types
- 2,801,388 sentence pairs in Japanese and English
- 337,039 illustration

### How this dataset was made?
1. Downloaded JESC dataset to get sentence pairs of English and Japanese
2. Found fonts from fonts website mentioned below
3. Downloaded Tagged Anime Illustrations dataset from Kaggle
4. Found and created different types of speech bubbles. Tagged which parts you can render text within.
5. Verified which fonts were viable and could cover at least 80% of the characters in the JESC dataset
6. Converted all the images to black and white 
7. Created default layout set/layouting engine to create pages 
8. Create metadata for these pages from the layouting engine and populate each panel with:
  1. What image the panel comprises of
  2. What textbubble is associated with it and it's metadata (font, text and render data)
9. Bounce page and it's panel's metadata to json in parallel.
9. Used renderer to create dataset from the generated json in parallel.

### Resources used for creating dataset:

1. [JESC dataset](https://nlp.stanford.edu/projects/jesc/)
2. [Tagged anime illustrations Kaggle dataset](https://www.kaggle.com/mylesoneill/tagged-anime-illustrations)
3. [Comic book pages Kaggle dataset](https://www.kaggle.com/cenkbircanoglu/comic-books-classification)
4. [Fonts allowed for commerical use from Free Japanese Fonts](https://www.freejapanesefont.com/) - Licences are on individual pages
5. [Object Detection for Comics using Manga109 Annotations](https://arxiv.org/pdf/1803.08670.pdf) - Used as benchmark
6. [Speech bubbles PSD file](https://www.deviantart.com/zombiesmile/art/300-Free-Speech-Bubbles-Download-419223430)
7. [Label studio](https://labelstud.io/)

### Licences and Citations
**JESC dataset**
```
@ARTICLE{pryzant_jesc_2017,
   author = {{Pryzant}, R. and {Chung}, Y. and {Jurafsky}, D. and {Britz}, D.},
    title = "{JESC: Japanese-English Subtitle Corpus}",
  journal = {ArXiv e-prints},
archivePrefix = "arXiv",
   eprint = {1710.10639},
 keywords = {Computer Science - Computation and Language},
     year = 2017,
    month = oct,
}             ```
```

[**Speech bubble PSD file Licence**](https://friendlystock.com/terms-of-use/)

### How does the layouting engine work?
1. Each Manga Page Image is represented by a JSON file. The page description contains the following
    1. Layout types and how they're denoted (here for easy search of particular panel types)
        1. Horizontal panels only - ```h```
        2. Vertical panel only - ```v```
        3. Vertical and horizontal panels - ```vh```
        4. All of the above with panel shape transforms - ```vht``` or ```ht```
          1. Slicing panels
          2. Turning full page panels into a a rhombus
          3. Turning full page panels zig-zag (future)
        5. All of the above on a background - ```vhtb```
        7. All of the above with white space insertions - ```vhtbw```
        8. Panel randomly overlaying each other (future)
        9. Figures across panels (future)
    2. Page size - Currently (1700 x 2400)
    3. Page type (currently only single page types as above)
    4. Panel boundary widths (future)
    5. Panel boundary types (future)
2. Each Page then has N panels which is determined by segmenting the page into rectangles from largest to smallest:
    1. Each panel has a rectangular baseline
      1. It's coordinates
      2. It's metadata e.g. Has it been transformed etc.
    2. Each panel also has a list of images that it's comprised of and how they've been inserted and speech bubbles around them
3. With the Panels each page also has a number of text bubbles on them. Usually the number being within (#panels-2 <= #bubbles <= #panels+2) of each panel on the depending on how large the panel is. Most bubbles are within the vicinity of a panel or within them with a small % of them peaking between panels. 
