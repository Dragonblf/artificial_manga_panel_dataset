import dask.dataframe as dd
import os
import paths


def convert_jesc_to_dataframe():
    """
    Convert the CSV file of the text to a
    Dask Dataframe
    """
    dataset_path = paths.DATASET_TEXT_FOLDER
    print("Loading data and converting to Dask Dataframe")
    filename = "raw.txt"
    df = dd.read_csv(dataset_path+filename, sep="\t")
    df.columns = ["English", "Japanese"]

    print("Saving data as Parquet archive")
    df.to_parquet(paths.DATASET_TEXT_JESC_DIALOGUES_FOLDER)
    os.remove(dataset_path+filename)
    os.remove(paths.DATASET_TEXT_RAW_JESC_DIALOGUES_FILE)
