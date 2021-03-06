"""
Functions for manipulating datasets.
"""
import itertools
import os
import shutil
from typing import List, Dict, Any
import json

import numpy as np
import pandas as pd
from PIL import Image

from .conversions import CONVERSIONS
from .lib import process_map
from .transforms import TRANSFORMS
from .store import CLASSES, DEFAULT_CLASS


def new_dataset(filenames: List[str], conversions: List[str],
                from_store=True) -> str:
    """
    Create a new dataset from a set of files and conversions.
    :param filenames: The list of files to import.
    :param conversions: The list of conversions to apply.
    :param from_store: Whether the images are from the store.
    :return: The path to the dataset folder.
    """
    # Create new dataset
    datasets = os.listdir("data/datasets")
    i = next(i for i in itertools.count() if f"dataset-{i}" not in datasets)
    dataset = f"data/datasets/dataset-{i}"
    os.mkdir(dataset)
    os.mkdir(f"{dataset}/images")
    with open(f"{dataset}/process.json", "w+") as f:
        json.dump(
            {"Conversions": conversions, "Transforms": [], "Bundled": None}, f)

    # Add images
    if from_store:
        df_store = pd.read_csv("data/log.csv", index_col="Index")
        df = df_store[[f in filenames for f in df_store["File"]]]
        conversions_left = [
            (r, [c for c in conversions if not r[c]])
            for _, r in df.iterrows()
        ]
    else:
        conversions_left = [({"File": f, "Class": DEFAULT_CLASS}, conversions)
                            for f in filenames]

    def _copy_and_apply(file: str, conversions_to_apply: List[str]) -> str:
        """
        Copies a file to a dataset and applies conversions.
        :param file: The file to copy and process.
        :param conversions_to_apply: The conversions to apply after copying.
        :return: None.
        """
        img = f"{dataset}/images/{os.path.basename(file)}"
        shutil.copyfile(file, img)
        for c in conversions_to_apply:
            img = CONVERSIONS[c](img)
        return img

    new_images = process_map(_copy_and_apply,
                             [(r["File"], cs) for r, cs in conversions_left],
                             packed=True)
    new_data = [(new, r["Class"]) for new, (r, _)
                in zip(new_images, conversions_left)]
    new_df = pd.DataFrame(new_data, columns=["File", "Class"])
    new_df.to_csv(f"{dataset}/log.csv", index_label="Index")
    return dataset


def delete_dataset(dataset: str) -> None:
    """
    Delete a dataset.
    :param dataset: The path to the dataset to delete.
    :return: None
    """
    shutil.rmtree(dataset)


def _load_image_array(fp: str) -> np.ndarray:
    """
    Converts an image on disk to a numpy array.
    :param fp: The image to convert.
    :return: The image data as a numpy array.
    """
    img = Image.open(fp)
    arr = np.array(img)
    img.close()
    return arr


def _make_imageset(dataset: str, transforms: List[str]) -> bool:
    """
    Loads the images from dataset image store, applies a series of transforms,
    and saves the result to the dataset.
    :param transforms: A list of transform functions to apply when loading.
    :param dataset: The path to the dataset.
    :return: Whether the operation was successful.
    """
    try:
        df = pd.read_csv(f"{dataset}/log.csv")
        fps = list(df["File"])
        images = process_map(_load_image_array, fps)
    except FileNotFoundError:
        return False
    for f in transforms:
        images = process_map(TRANSFORMS[f], images)
    with open(f"{dataset}/process.json", "r") as f:
        data = json.load(f)
        data["Transforms"] = transforms
    with open(f"{dataset}/process.json", "w+") as f:
        json.dump(data, f)
    np.save(f"{dataset}/X.npy", np.array(images))
    return True


def _make_labelset(dataset: str, bundled: bool = True) -> bool:
    """
    Turns the labels of a dataset into training data labels, applying bundling
    of chart classes if desired.
    :param dataset: The dataset to create label data for.
    :param bundled: Whether the chart classes should be bundled.
    :return: Whether the operation was successful.
    """
    df = pd.read_csv(f"{dataset}/log.csv")
    classes = [int(bool(CLASSES[c])) if bundled else CLASSES[c] for c in
               df["Class"]]
    with open(f"{dataset}/process.json", "r") as f:
        data = json.load(f)
        data["Bundled"] = bundled
    with open(f"{dataset}/process.json", "w+") as f:
        json.dump(data, f)
    np.save(f"{dataset}/Y.npy", np.array(classes))
    return True


def make_data(dataset: str, transforms: List[str],
              bundled: bool = True) -> bool:
    """
    Construct X.npy and Y.npy dataset files.
    :param dataset: The dataset to convert.
    :param transforms: The list of transforms to apply to the images.
    :param bundled: Whether the label classes should be bundled.
    :return: Whether the operation was successful.
    """
    return _make_imageset(dataset, transforms) and \
           _make_labelset(dataset, bundled)


def get_process(dataset: str) -> Dict[str, Any]:
    """
    Returns the process metadata object for a dataset.
    :param dataset: The dataset to read the process of.
    :return: An object containing a list of conversions and transforms and
    whether the classes are bundled for the given dataset.
    """
    with open(f"{dataset}/process.json", "r") as f:
        data = json.load(f)
    return data
