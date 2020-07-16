import os
import shutil
from typing import Callable, List, Optional
import multiprocessing
from PIL import Image

# Process count for multiprocessing
POOL_SIZE = 4
# Scaling dimensions
HEIGHT = 300
WIDTH = 400


def _create_tmp() -> None:
    """
    If no temporary folder exists, create one.
    :return: None.
    """
    try:
        os.mkdir("tmp")
    except FileExistsError:
        pass


def copy_to_tmp(fp: str) -> str:
    """
    Copies an image to temporary folder.
    :param fp: The image to copy.
    :return: A path to the new image.
    """
    new_path = f"tmp/{os.path.basename(fp)}"
    try:
        shutil.copyfile(fp, new_path)
    except FileNotFoundError:
        _create_tmp()
        shutil.copyfile(fp, new_path)
    return new_path


def convert_to_png(fp: str) -> str:
    """
    Destructively converts an image to a PNG.
    :param fp: The path to the image to convert.
    :return: The path to the converted image.
    """
    new_fp = f"{'.'.join(fp.split('.')[:-1])}.png"

    img = Image.open(fp)
    img.load()  # Force loading of the image into memory
    img.save(new_fp, format="png")
    img.close()

    os.remove(fp)

    return new_fp


def make_grayscale(fp: str, dest: Optional[str] = None) -> str:
    """
    Converts an image to single-channel grayscale. In-place if no destination
    path is specified.
    :param fp: The image to convert.
    :param dest: A destination path, if a non-destructive operation is desired.
    :return: The path to the new image.
    """
    img = Image.open(fp)
    img = img.convert("L")
    new_path = dest or fp
    img.save(new_path)
    return new_path


def scale_image(fp: str, dest: Optional[str] = None) -> str:
    """
    Scales an image to HEIGHT x WIDTH, the standard size used by the pipeline
    for modelling.
    :param fp: The image to convert.
    :param dest: A destination path, if a non-destructive operation is desired.
    :return: The path to the new image.
    """
    img = Image.open(fp)
    img = img.resize((WIDTH, HEIGHT))
    new_path = dest or fp
    img.save(new_path)
    return new_path


def process_map(f: Callable, args: List, packed: bool = False) -> List:
    """
    Maps an operation from processing.py across multiple processes.
    :param f: The function to map, from processing.py.
    :param args: The list of argument tuples to map over.
    :param packed: Whether the args list consists of packed argument tuples.
    :return: The list of outputs from the mapping of f over args.
    """
    with multiprocessing.Pool(POOL_SIZE) as p:
        if packed:
            return p.starmap(f, args)
        else:
            return p.map(f, args)