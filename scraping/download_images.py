import os
import paths
import shutil


def download_db_illustrations():
    """
    Downloads the Tagged Anime Illustrations Kaggle dataset
    """

    kaggle_json = "config/kaggle.json"
    if not os.path.isfile(kaggle_json):
        print("Please create a config folder in this directory\
               and add your kaggle credentials")
        return

    zip_file = paths.DATASET_IMAGES_RAW_FOLDER + "tagged-anime-illustrations.zip"
    if not os.path.isfile(zip_file):
        os.environ['KAGGLE_CONFIG_DIR'] = "config/"

        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        api.authenticate()

        dataset = "mylesoneill/tagged-anime-illustrations"
        api.dataset_download_files(dataset,
                                   path=paths.DATASET_IMAGES_RAW_FOLDER,
                                   quiet=False,
                                   unzip=False
                                   )

    print("Finished downloading now unzipping")
    output_dir = paths.DATASET_IMAGES_DANBOORU_COLORED_IMAGES_FOLDER

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    os.system("unzip -o "+zip_file + " -d "+output_dir)
    print("Finished unzipping")


def remove_temporary_image_directories():
    print("Deleting raw image folder...")
    shutil.rmtree(paths.DATASET_IMAGES_RAW_FOLDER)


def download_speech_bubbles():
    pass
