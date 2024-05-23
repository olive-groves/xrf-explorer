import logging

import numpy as np

from os.path import isfile
from pathlib import Path

from xrf_explorer.server.file_system.from_csv import get_raw_elemental_data_cube_from_csv, get_elements_from_csv
from xrf_explorer.server.file_system.from_dms import get_raw_elemental_data_cube_from_dms, get_elements_from_dms

LOG: logging.Logger = logging.getLogger(__name__)


def normalize_ndarray_to_grayscale(array: np.ndarray) -> np.ndarray:
    """Map all values in the given array to the interval [0, 255].
    
    :param array: n-dimensional numpy array.
    :return: a copy of the array with values mapped to the interval [0, 255].
    """

    # normalize data
    (min, max) = array.min(), array.max()
    normalized_array: np.ndarray = (array - min) / (max - min)

    # obtain image of elemental abundance at every pixel of elemental image
    return np.rint(normalized_array * 255).astype(np.uint8)


def normalize_elemental_cube_total_cube(raw_cube: np.ndarray) -> np.ndarray:
    """Normalize the raw elemental data cube.

    :param raw_cube: 3-dimensional numpy array containing the normalized elemental data. First dimension
    is channel, and last two for x, y coordinates.
    :return: 3-dimensional numpy array containing the normalized elemental data. First dimension
    is channel, and last two for x, y coordinates.
    """

    return normalize_ndarray_to_grayscale(raw_cube)


def normalize_elemental_cube_per_layer(raw_cube: np.ndarray) -> np.ndarray:
    """Normalize the raw elemental data cube.

    :param raw_cube: 3-dimensional numpy array containing the normalized elemental data. First dimension
    is channel, and last two for x, y coordinates.
    :return: 3-dimensional numpy array containing the normalized elemental data. First dimension
    is channel, and last two for x, y coordinates.
    """

    normalized_cube: np.ndarray = np.zeros(raw_cube.shape, dtype=np.uint8)
    number_of_channels = raw_cube.shape[0]

    for i in range(number_of_channels):
        normalized_cube[i] = normalize_ndarray_to_grayscale(raw_cube[i])

    return normalized_cube


def get_elemental_data_cube(path: str | Path) -> np.ndarray:
    """Get the elemental data cube at the given path.

    :param path: Path to the file containing the elemental data cube.
    :return: 3-dimensional numpy array containing the elemental data cube. First dimension
    is channel, and last two for x, y coordinates.
    """

    # Check if the file exists
    if not isfile(str):
        return np.empty(0)
    
    # Return the elemental data cube
    if path.endswith('.csv'):
        return get_raw_elemental_data_cube_from_csv(path)
    elif path.endswith('.dms'):
        return get_raw_elemental_data_cube_from_dms(path)
    else:
        return np.empty(0)


def get_element_names(path: str | Path) -> list[str]:
    """Get the names of the elements stored in the elemental data cube.
    
    :param path: Path to the elemental data cube.
    :return: List of the names of the elements. Empty list if error occured.
    """

    # Check if the file exists
    if not isfile(str):
        return []
    
    # Return the elemental data cube
    if path.endswith('.csv'):
        return get_elements_from_csv(path)
    elif path.endswith('.dms'):
        return get_elements_from_dms(path)
    else:
        return []


def get_short_element_names(path: str | Path) -> list[str]:
    """Get the short names of the elements stored in the elemental data cube.
    
    :param path: Path to the elemental data cube.
    :return: List of the names of the elements. Empty list if error occured.
    """

    # Get regular names
    element_names: list[str] = get_element_names(path)

    short_names: list[str] = []

    # Make names shorter
    for name in element_names:
        short_name = name.replace(" ", "")

        if short_name == "Continuum":
            short_names.append("cont.")
        elif short_name == "chisq":
            short_names.append("chi")
        else:
            short_names.append(short_name)
   
    return short_names


def get_element_averages(path: str | Path) -> list[dict[str, str | float]]:
    """Get the names and averages of the elements present in the painting.

    :param path: path to the elemental data cube.
    :return: List of the names and average composition of the elements.
    """

    image_cube: np.ndarray = get_elemental_data_cube(path)
    names: list[str] = get_element_names(path)

    # Check if the data was loaded correctly
    if image_cube.size == 0 or names == []:
        LOG.error(f"Couldn't parse elemental image cube or list of names")
        return []

    # Calculate the average composition of the elements
    averages: np.ndarray = np.mean(image_cube, axis=(1, 2))
    
    # Create a list of dictionaries with the name and average composition of the elements
    composition: list[dict[str,  str | float]] = \
        [{"name": names[i], "average": averages[i]} for i in range(averages.size)]

    return composition
