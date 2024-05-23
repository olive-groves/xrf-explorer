import logging

from os.path import isfile
from pathlib import Path

import csv

import numpy as np
import pandas as pd

LOG: logging.Logger = logging.getLogger(__name__)


def get_elements_from_csv(path: str | Path) -> list[str]:
    """Get the names of the elements stored in the elemental data cube.
    
    :param path: Path to the csv file containing the elemental data cube.
    :return: List of the names of the elements. Empty list if error occured.
    """
    
    LOG.info(f"Reading elements from {path}")

    # Check if the file exists
    if not isfile(path):
        LOG.error(f"File not found: {path}")
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


def get_raw_elemental_data_cube_from_csv(path: str | Path) -> np.ndarray:
    """Get the elemental data cube from the csv file.

    :param path: Path to the csv file containing the elemental data cube.
    :return: 3-dimensional numpy array containing the normalized elemental data. First dimension
    is channel, and last two for x, y coordinates.
    """

    LOG.info(f"Reading elemental data cube from {path}")

    # Check if the file exists
    if not isfile(path):
        LOG.error(f"File not found: {path}")
        return []
    
    # Can give an error for bad csv files, but type of Exception is not specified
    try:
        # Read the csv file. Pandas is used, since numpy is slow at reading csv files.
        e = pd.read_csv(path, sep=';', header=0, index_col=False, dtype=np.float32).set_index(["row", "column"])

        # Get width and height of the elemental cube
        height, width = len(e.index.levels[0]), len(e.index.levels[1])

        # Reshape the elemental cube
        raw_elemental_cube = e.to_numpy().reshape(height, width, -1).swapaxes(0, 2)

        LOG.info(f"Elemental data cube loaded with shape: {raw_elemental_cube.shape}")

        return raw_elemental_cube
    
    except Exception as e:
        LOG.error(f"Error reading csv file: {str(e)}")
        return []
