"""
Functions for constructing datasets.
"""
from typing import List
import json

import numpy as np
import pandas as pd
from PIL import Image

from .lib import process_map
from .transforms import TRANSFORMS


def load_image_array(fp: str) -> np.ndarray:
    """
    Converts an image on disk to a numpy array.
    :param fp: The image to convert.
    :return: The image data as a numpy array.
    """
    img = Image.open(fp)
    arr = np.array(img)
    img.close()
    return arr


def make_imageset(dataset: str, transforms: List[str]) -> bool:
    """
    Loads the images from a set of URLS, applies a series of transforms, and
    saves the result to the dataset.
    :param transforms: A list of transform functions to apply when loading.
    :param dataset: The path to the dataset.
    :return: Whether the operation was successful.
    """
    try:
        df = pd.read_csv(f"{dataset}/log.csv")
        fps = list(f"{dataset}/images/{f}" for f in df["File"])
        images = process_map(load_image_array, fps)
    except FileNotFoundError:
        return False
    for f in transforms:
        images = process_map(TRANSFORMS[f], images)
    with open(f"{dataset}/process.json", "r+") as f:
        data = json.load(f)
        data["Transforms"] = transforms
        json.dump(data, f)
    np.save(f"{dataset}/X.npy", np.array(images))
    return True
