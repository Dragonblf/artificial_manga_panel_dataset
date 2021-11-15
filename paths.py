import os

# DATASET PATHS #
dataset_folder = "dataset/"
dataset_font_folder = dataset_folder + "fonts/"
dataset_text_folder = dataset_folder + "texts/"
dataset_images_folder = dataset_folder + "images/"
dataset_text_jesc_dialogues_folder = dataset_text_folder + "jesc_dialogues"
dataset_speech_bubbles_folder = "datasets/speech_bubbles/"

dataset_folder_paths = [dataset_font_folder, dataset_text_folder,
                        dataset_images_folder, dataset_speech_bubbles_folder,
                        dataset_text_jesc_dialogues_folder]

# DATASET PATHS #
generated_folder = "generated/"
generated_images_folder = generated_folder + "images/"
generated_metadata_folder = generated_folder + "metadata/"

generated_folder_paths = [generated_metadata_folder, generated_images_folder]


def makeFolders(folders):
    for path in folders:
        if not os.path.exists(path):
            os.makedirs(path)
