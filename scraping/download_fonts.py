import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import os
import paths

preview_page_file = paths.DATASET_FONTS_FOLDER + "browse_links.txt"
font_links_file = paths.DATASET_FONTS_FOLDER + "font_links.txt"
font_file_raw_downloads = paths.DATASET_FONTS_ZIPPED_FOLDER


def get_browse_page_links():
    """Goes through pages of freejapanesefont.com and
    downloads each individual link to a font file page
    """
    root_url = "https://www.freejapanesefont.com/"
    total_pages = 23

    links = []
    for page_num in tqdm(range(1, total_pages+1)):
        page_name = root_url + "page/" + str(page_num)

        resp = requests.get(page_name)

        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, features="html.parser")
            link_divs = soup.find_all("div", "preview")
            for div in link_divs:
                links.append(list(div.children)[1]['href'])

    with open(preview_page_file, "w+") as links_file:
        for link in links:
            links_file.write(link+"\n")


def getFileFromMediafire(url, path):
    resp = requests.get(url)
    soup = BeautifulSoup(resp.content, features="html.parser")
    file = soup.find("a", id="downloadButton", href=True)["href"]
    file_name = file.split("/")[-1]
    print("Downloading " + file_name + "...")
    myfile = requests.get(file)
    open(path + file_name, 'wb').write(myfile.content)
    print(file_name + " downloaded")


def get_browse_page_links2():
    """Goes through pages of freejapanesefont.com and
    downloads each individual link to a font file page
    """

    page_name = "https://learnjapanesedaily.com/beautiful-japanese-font.html"
    resp = requests.get(page_name)

    if resp.status_code == 200:
        soup = BeautifulSoup(resp.content, features="html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "mediafire" in href and ".zip" in href:
                getFileFromMediafire(href, path=font_file_raw_downloads)


def get_font_links():
    """
    Wrapper for get_brower_page_links
    TODO: Add scraping of individual font
    file links
    """

    dir = os.listdir(font_file_raw_downloads)

    if len(dir) == 0:
        print("Getting font preview pages")
        get_browse_page_links2()
    else:
        print("Fonts already downloaded")

    # if not os.path.isfile(preview_page_file):
    #     print("Getting font preview pages")
    #     get_browse_page_links()
    # else:
    #     print("Font preview pages txt exists")
