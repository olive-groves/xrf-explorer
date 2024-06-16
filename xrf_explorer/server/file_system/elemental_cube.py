import logging

from os import remove
from os.path import join, isdir, basename, splitext, dirname

import json
import numpy as np

from xrf_explorer.server.file_system.file_access import get_path_to_workspace, get_elemental_cube_path_from_name
from xrf_explorer.server.file_system.from_csv import (
    get_raw_elemental_data_cube_from_csv, get_raw_elemental_map_from_csv,
    get_elements_from_csv)
from xrf_explorer.server.file_system.from_dms import (
    get_raw_elemental_data_cube_from_dms, get_raw_elemental_map_from_dms, 
    get_elements_from_dms)

LOG: logging.Logger = logging.getLogger(__name__)


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


def get_elemental_data_cube(path: str) -> np.ndarray:
    """Get the elemental data cube at the given path.

    :param path: Path to data cube.
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


def get_elemental_map(element: int, path: str) -> np.ndarray:
    """Get the elemental map of element index at the given path.

    :param element: Index of the element in the elemental data cube.
    :param path: Path to data cube.
    :return: 2-dimensional numpy array containing the elemental data cube. Dimensions are the x, y coordinates.
    """
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


def get_element_names(path: str) -> list[str]:
    """Get the names of the elements stored in the elemental data cube.
    
    :param path: Path to data cube.
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


def get_short_element_names(path: str) -> list[str]:
    """Get the short names of the elements stored in the elemental data cube.
    
    :param path: Path to data cube.
    :return: List of the names of the elements. Empty list if error occurred.
    """
    # Get regular names
    element_names: list[str] = get_element_names(path)
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


def get_element_averages(path: str) -> list[dict[str, str | float]]:
    """Get the names and averages of the elements present in the painting.
    :param path: Path to data cube.
    :return: List of the names and average composition of the elements.
    """

    # Get the elemental data cube and the names of the elements
    raw_cube: np.ndarray = get_elemental_data_cube(path)
    names: list[str] = get_element_names(path)

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
        [{"name": names[i], "average": float(averages[i])} for i in range(averages.size)]
    
    LOG.info("Calculated the average composition of the elements.")

    return composition


def get_element_averages_selection(selection: np.ndarray, names: list[str]) -> list[dict[str, str | float]]:
    """Get the names and averages of the elements present in (a subarea of) the painting.
    :param selection: A 2D array where the rows represent the selected pixels from the data cube image and the columns represent their elemental map values.
    :param names: The names of the elements present in the painting.
    :return: List of the names and average composition of the elements.
    """
    # Return zeroes if selection is empty
    if selection.size == 0:
        return [{"name": names[i], "average": 0.0} for i in range(len(names))]

    # Calculate the average composition of each element in the selection
    averages: np.ndarray = np.mean(selection, axis=1)

    # Create a list of dictionaries with the name and average composition of the elements
    composition: list[dict[str,  str | float]] = \
        [{"name": names[i], "average": float(averages[i])} for i in range(averages.size)]

    LOG.info("Calculated the average composition of the elements within selection.")

    return composition


def convert_elemental_cube_to_dms(data_source: str, cube_name: str) -> bool:
    """Converts an elemental data cube to .dms format. Updates the workspace accordingly and removes the old elemental data cube.

    :param data_source: Name of the data source.
    :param cube_name: Name of the elemental data cube. Should be present in the workspace.
    :return: True if the cube was converted successfully, False otherwise.
    """

    # Get the path to the elemental data cube
    cube_path: str | None = get_elemental_cube_path_from_name(data_source, cube_name)
    if cube_path is None:
        return False

    # Get the elemental data cube and the names of the elements from the file of the given type
    cube: np.ndarray
    element_names: list[str]

    # If the file is already in .dms format, return True
    if cube_path.endswith(".dms"):
        return True
    
    # Check other file types
    if cube_path.endswith(".csv"):
        # Convert elemental data cube to .dms format
        cube = get_elemental_data_cube(cube_path)
        element_names = get_element_names(cube_path)
    else:
        LOG.error(f"Cannot convert {cube_path} to .dms format.")
        return False
    
    # Check if the data was loaded correctly
    if cube is np.empty(0) or len(element_names) == 0:
        return False
    
    # Save the elemental data cube with elements to a .dms file
    file_name: str = splitext(basename(cube_path))[0]
    success: bool = to_dms(dirname(cube_path), file_name, cube, element_names)
    if not success:
        return False
    
    # Update workspace
    workspace_path: str = get_path_to_workspace(data_source)
    if not workspace_path:
        return False

    try:
        with open(workspace_path, "r+") as file:
            workspace: dict = json.load(file)

            # Find the correct elemental data cube
            for cube_info in workspace["elementalCubes"]:
                if cube_info["name"] == cube_name:
                    cube_info["dataLocation"] = f"{file_name}.dms"
                    break

            file.seek(0)
            file.write(json.dumps(workspace))
            file.truncate()
    except Exception as e:
        LOG.error(f"Failed to update workspace: {str(e)}")
        return False

    # Remove the old elemental data cube
    remove(cube_path)

    LOG.info(f"Converted {cube_path} to .dms format.")
    return True


def to_dms(folder_path: str, name_cube: str, cube: np.ndarray, elements: list[str]) -> bool:
    """Saves a numpy array and list of elements to a DMS file.

    :param folder_path: Path to the folder where the DMS file will be saved.
    :param name_cube: Name of the elemental data cube. Without file extension, e.g. 'cube'.
    :param cube: 3-dimensional numpy array containing the elemental data cube. First dimension is channel, and last two for x, y coordinates.
    :param elements: List of the names of the elements.
    :return: True if the cube was saved successfully, False otherwise.
    """

    if not isdir(folder_path):
        LOG.error(f"Folder {folder_path} does not exist.")
        return False

    if "." in name_cube:
        LOG.error("Name of the cube should not contain a file extension.")
        return False
    
    path_cube: str = join(folder_path, name_cube + '.dms')
    
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
