import logging

import numpy as np
import json

from os.path import isfile, join
from pathlib import Path

from xrf_explorer.server.file_system.config_handler import load_yml
from xrf_explorer.server.file_system.from_csv import (
    get_raw_elemental_data_cube_from_csv, get_raw_elemental_map_from_csv,
    get_elements_from_csv)
from xrf_explorer.server.file_system.from_dms import (
    get_raw_elemental_data_cube_from_dms, get_raw_elemental_map_from_dms, 
    get_elements_from_dms)

LOG: logging.Logger = logging.getLogger(__name__)
BACKEND_CONFIG: dict = load_yml("config/backend.yml")


def normalize_ndarray_to_grayscale(array: np.ndarray) -> np.ndarray:
    """Map all values in the given array to the interval [0, 255].
    
    :param array: n-dimensional numpy array.
    :return: a copy of the array with values mapped to the interval [0, 255].
    """

    # normalize data
    (min_val, max_val) = array.min(), array.max()
    normalized_array: np.ndarray = (array - min_val) / (max_val - min_val)

    # obtain image of elemental abundance at every pixel of elemental image
    return np.rint(normalized_array * 255).astype(np.uint8)


def normalize_elemental_cube_per_layer(raw_cube: np.ndarray) -> np.ndarray:
    """Normalize the raw elemental data cube.

    :param raw_cube: 3-dimensional numpy array containing the normalized elemental data. First dimension is channel, and last two for x, y coordinates.
    :return: 3-dimensional numpy array containing the normalized elemental data. First dimension is channel, and last two for x, y coordinates.
    """

    # Initialize the normalized cube
    normalized_cube: np.ndarray = np.zeros(raw_cube.shape, dtype=np.uint8)

    # Get number of channels
    number_of_channels: int = raw_cube.shape[0]

    # Normalize each channel separately
    for i in range(number_of_channels):
        normalized_cube[i] = normalize_ndarray_to_grayscale(raw_cube[i])

    return normalized_cube


def get_path_to_elemental_cube(name_cube: str, config_path: str = "config/backend.yml") -> str:
    """Get the path to the elemental data cube.

    :param name_cube: Name of the elemental data cube.
    :param config_path: Path to the backend config file.
    :return: Path to the elemental data cube.
    """

    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return ""
    
    # path to cube 
    path_cube: str = join(Path(backend_config['uploads-folder']), name_cube)

    # Check if the file exists
    if not isfile(path_cube):
        LOG.error(f"File not found: {path_cube}")
        return ""

    return path_cube

def get_data_cube_path(data_source: str) -> str:
    """Get the location of the datacube file (.dms) of a given datasource
    
    :param datasource: Name of the datasource.
    :return: Path string pointing to the datacube location.
    """
    data_source_dir = join(Path(BACKEND_CONFIG["uploads-folder"]), data_source, "workspace.json")
    try:
        with open(data_source_dir, 'r') as workspace:
            data_json = workspace.read()
            data = json.loads(data_json)
            data_cube_name = data["elementalCubes"][0]["dataLocation"]
    except OSError as err:
        LOG.error("Error while getting dms file location: {%s}", err)
        return 400
    
    path = join(BACKEND_CONFIG["uploads-folder"], data_source, data_cube_name)
    return path

def get_elemental_data_cube(path: str, config_path: str = "config/backend.yml") -> np.ndarray:
    """Get the elemental data cube at the given path.

    :param path: Path to data cube.
    :param config_path: Path to the backend config file.
    :return: 3-dimensional numpy array containing the elemental data cube. First dimension is channel, and last two for x, y coordinates.
    """
    
    # Get the elemental data cube
    elemental_cube: np.ndarray

    LOG.info(f"Reading elemental data cube from {path}")

    try:
        # Choose the correct method to read the elemental data cube
        if path.endswith('.csv'):
            elemental_cube = get_raw_elemental_data_cube_from_csv(path)
        elif path.endswith('.dms'):
            elemental_cube = get_raw_elemental_data_cube_from_dms(path)
        else:
            elemental_cube = np.empty(0)

    except Exception as e:
        LOG.error(f"Error while reading elemental data cube: {e}")
        return np.empty(0)
    
    LOG.info(f"Elemental data cube loaded. Shape: {elemental_cube.shape}")

    return elemental_cube


def get_elemental_map(element: int, name_cube: str, config_path: str = "config/backend.yml") -> np.ndarray:
    """Get the elemental map of element index at the given path.

    :param element: Index of the element in the elemental data cube.
    :param name_cube: Name of the elemental data cube.
    :param config_path: Path to the backend config file.
    :return: 2-dimensional numpy array containing the elemental data cube. Dimensions are the x, y coordinates.
    """

    # Get full path to the elemental data cube
    path: str = get_path_to_elemental_cube(name_cube, config_path)
    if not path:
        return np.empty(0)
    
    # Get the elemental data cube
    elemental_cube: np.ndarray

    LOG.info(f"Reading elemental map of element {element} from {path}")
    
    try:
        # Choose the correct method to read the elemental map
        if path.endswith('.csv'):
            elemental_cube = get_raw_elemental_map_from_csv(element, path)
        elif path.endswith('.dms'):
            elemental_cube = get_raw_elemental_map_from_dms(element, path)
        else:
            elemental_cube = np.empty(0)

    except Exception as e:
        LOG.error(f"Error while reading elemental map: {e}")
        return np.empty(0)
    
    LOG.info(f"Elemental map loaded. Shape: {elemental_cube.shape}")

    return elemental_cube


def get_element_names(path: str, config_path: str = "config/backend.yml") -> list[str]:
    """Get the names of the elements stored in the elemental data cube.
    
    :param path: path to the elemental data cube.
    :param config_path: Path to the backend config file.
    :return: List of the names of the elements. Empty list if error occurred.
    """
    
    # Return the elemental data cube
    elements: list[str]

    LOG.info(f"Reading elements from {path}")

    try:
        # Choose the correct method to read the elemental names
        if path.endswith('.csv'):
            elements = get_elements_from_csv(path)
        elif path.endswith('.dms'):
            elements = get_elements_from_dms(path)
        else:
            elements = []
    
    except Exception as e:
        LOG.error(f"Could not read elemental data cube: {e}")
        return []
    
    LOG.info(f"Elements loaded. Total elements: {len(elements)}")

    return elements


def get_short_element_names(path: str, config_path: str = "config/backend.yml") -> list[str]:
    """Get the short names of the elements stored in the elemental data cube.
    
    :param path: Path to data cube.
    :param config_path: Path to the backend config file.
    :return: List of the names of the elements. Empty list if error occurred.
    """

    # Get regular names
    element_names: list[str] = get_element_names(path, config_path)
    if element_names == []:
        return []

    short_names: list[str] = []

    # Make names shorter
    for name in element_names:
        short_name: str = name.replace(" ", "")

        if short_name == "Continuum":
            short_names.append("cont.")
        elif short_name == "chisq":
            short_names.append("chi")
        else:
            short_names.append(short_name)
   
    return short_names


def get_element_averages(data_source: str, config_path: str = "config/backend.yml") -> list[dict[str, str | float]]:
    """Get the names and averages of the elements present in the painting.

    :param data_source: Name of the data source.
    :param config_path: Path to the backend config file.
    :return: List of the names and average composition of the elements.
    """

    # Get the elemental data cube and the names of the elements
    raw_cube: np.ndarray = get_elemental_data_cube(data_source, config_path)
    names: list[str] = get_element_names(data_source, config_path)

    # Check if the data was loaded correctly
    if raw_cube.size == 0 or names == []:
        LOG.error(f"Couldn't parse elemental image cube or list of names")
        return []
    
    # Normalize the elemental data cube
    image_cube: np.ndarray = normalize_ndarray_to_grayscale(raw_cube)

    # Calculate the average composition of the elements
    averages: np.ndarray = np.mean(image_cube, axis=(1, 2))
    
    # Create a list of dictionaries with the name and average composition of the elements
    composition: list[dict[str,  str | float]] = \
        [{"name": names[i], "average": averages[i]} for i in range(averages.size)]

    LOG.info("Calculated the average composition of the elements.")

    return composition


def to_dms(name_cube: str, cube: np.ndarray, elements: list[str], config_path: str = "config/backend.yml") -> bool:
    """"Saves a numpy array and list of elements to a DMS file.

    :param name_cube: Name of the elemental data cube. Without file extension, e.g. 'cube'.
    :param cube: 3-dimensional numpy array containing the elemental data cube. First dimension is channel, and last two for x, y coordinates.
    :param elements: List of the names of the elements.
    :param config_path: Path to the backend config file.
    :return: True if the cube was saved successfully, False otherwise.
    """

    if "." in name_cube:
        LOG.error("Name of the cube should not contain a file extension.")
        return False
    
    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return False
    
    # path to cube 
    path_cube: str = join(Path(backend_config['uploads-folder']), name_cube + '.dms')
    
    # Get the shape of the elemental data cube
    c, w, h = cube.shape

    # Write the elemental data cube to a DMS file
    try:
        with open(path_cube, 'wb+') as f:
            f.write(b'2\n')
            f.write("{0} {1} {2}\n".format(w, h, c).encode())
            f.write(cube.tobytes())
            f.write('\n'.join(elements).encode())
    except OSError as e:
        LOG.error(f"Error while writing elemental map to dms: {e}")
        return False

    return True
