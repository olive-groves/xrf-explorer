import logging

from os.path import isfile
from pathlib import Path

import csv

import numpy as np
import pandas as pd

LOG: logging.Logger = logging.getLogger(__name__)


def normalize_elemental_cube(raw_cube: np.ndarray) -> np.ndarray:
    """Normalize the raw elemental data cube.

    :param raw_cube: 3-dimensional numpy array containing the raw elemental data. First 2 dimensions
    are x, y coordinates, last dimension is for channels i.e. elements.
    :return: 3-dimensional numpy array containing the normalized elemental data. First 2 dimensions
    are x, y coordinates, last dimension is for channels i.e. elements.
    """

    # normalize data
    (raw_data_min, raw_data_max) = raw_cube.min(), raw_cube.max()
    normalized_data: np.ndarray = (raw_cube - raw_data_min) / (raw_data_max - raw_data_min)

    # obtain image of elemental abundance at every pixel of elemental image
    return np.rint(normalized_data * 255).astype(np.uint8)


def valid_csv_file(path: str | Path) -> bool:
    """Check if the file is a valid csv file.
    
    :param path: Path to the file.
    :return: True if the file is a valid csv file, False otherwise.
    """

    # Check if the file exists
    if not isfile(path):
        LOG.error(f"File not found: {path}")
        return False
    
    # Check if the file is a csv file
    if not path.endswith('.csv'):
        LOG.error(f"File is not a csv file: {path}")
        return False
    
    return True


def get_elements_from_csv(path: str | Path) -> list[str]:
    """Get the names of the elements stored in the elemental data cube.
    
    :param path: Path to the csv file containing the elemental data cube.
    :return: List of the names of the elements. Empty list if error occured.
    """
    
    LOG.info(f"Reading elements from {path}")

    # Check if the file exists
    if not valid_csv_file(path):
        return []
    
    with open(path, 'r') as f:
        # Try to open the csv reader
        try:
            # Create csv reader. The data is separated by ';'
            csvreader: csv._reader = csv.reader(f, delimiter=';')

            # Columns names are on the first row
            column_names: list[str] = csvreader.__next__()
            LOG.info(f"Elements loaded. Total elements: {len(column_names) - 2}")
            
            # First two columns are not for elements
            return column_names[2:]

        except csv.Error as e:
            LOG.error(f"Error reading csv file: {str(e)}")
    
    # If reading csv fails return empty list
    return []


def get_elemental_data_cube(path: str | Path) -> np.ndarray:
    """Get the elemental data cube from the csv file.

    :param path: Path to the csv file containing the elemental data cube.
    :return: 3-dimensional numpy array containing the normalized elemental data. First 2 dimensions
    are x, y coordinates, last dimension is for channels i.e. elements.
    """

    LOG.info(f"Reading elemental data cube from {path}")

    # Check if the file exists
    if not valid_csv_file(path):
        return []
    
    # Can give an error for bad csv files, but type of Exception is not specified
    try:
        # Read the csv file. Pandas is used, since numpy is slow at reading csv files.
        e = pd.read_csv(path, sep=';', header=0, index_col=False, dtype=np.float32).set_index(["row", "column"])

        # Get width and height of the elemental cube
        height, width = len(e.index.levels[0]), len(e.index.levels[1])

        # Reshape the elemental cube
        raw_elemental_cube = e.to_numpy().reshape(height, width, -1).swapaxes(0, 1)

        # Normalize the elemental cube
        elemental_cube = normalize_elemental_cube(raw_elemental_cube)

        LOG.info(f"Elemental data cube loaded with shape: {elemental_cube.shape}")

        return elemental_cube
    
    except Exception as e:
        LOG.error(f"Error reading csv file: {str(e)}")
        return []
