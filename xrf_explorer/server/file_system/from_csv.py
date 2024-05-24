from pathlib import Path

import csv

import numpy as np
import pandas as pd


def get_elements_from_csv(path: str | Path) -> list[str]:
    """Get the names of the elements stored in the elemental data cube.
    Can raise error if file could not be read.
    
    :param path: Path to the csv file containing the elemental data cube.
    :return: List of the names of the elements.
    """
    
    with open(path, 'r') as f:
        # Create csv reader. The data is separated by ';'
        csvreader: csv._reader = csv.reader(f, delimiter=';')

        # Columns names are on the first row
        column_names: list[str] = csvreader.__next__()
        
        # First two columns are not for elements
        return column_names[2:]


def get_raw_elemental_data_cube_from_csv(path: str | Path) -> np.ndarray:
    """Get the elemental data cube from the csv file at the given path.
    Can raise error if file could not be read.

    :param path: Path to the csv file containing the elemental data cube.
    :return: 3-dimensional numpy array containing the elemental data cube. First dimension
    is channel, and last two for x, y coordinates.
    """
    
    # Read the csv file. Pandas is used, since numpy is slow at reading csv files.
    df_cube: pd.DataFrame = pd.read_csv(
            path, sep=';', header=0, index_col=False, dtype=np.float32
        ).set_index(["row", "column"])

    # Get width and height of the elemental cube
    height, width = len(df_cube.index.levels[0]), len(df_cube.index.levels[1])

    # Reshape the elemental cube
    return df_cube.to_numpy().reshape(height, width, -1).swapaxes(0, 2)


def get_raw_elemental_map_from_csv(element: int, path: str | Path) -> np.ndarray:
    """Get the elemental map of the given element from the csv file.
    Can raise error if file could not be read.

    :param element: Index of the element in the elemental data cube.
    :param path: Path to the dms file containing the elemental data cube.
    :return: 2-dimensional numpy array containing the elemental map. Dimensions
    are the x, y coordinates.
    """

    # column of element index is two more, since first two columns are "row" and "column"
    column_element: int = element + 2

    # Read the csv file. Pandas is used, since numpy is slow at reading csv files.
    df_cube: pd.DataFrame = pd.read_csv(
        path, sep=';', usecols=[0, 1, column_element], 
        header=0, index_col=False, dtype=np.float32
    ).set_index(["row", "column"])

    # Get width and height of the elemental cube
    height, width = len(df_cube.index.levels[0]), len(df_cube.index.levels[1])

    # Reshape the elemental cube
    return df_cube.to_numpy().reshape(height, width).swapaxes(0, 1)
