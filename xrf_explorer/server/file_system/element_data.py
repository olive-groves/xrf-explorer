import logging

from os.path import join, abspath
from pathlib import Path

import numpy as np

from xrf_explorer.server.file_system.config_handler import load_yml

LOG: logging.Logger = logging.getLogger(__name__)


def get_raw_elemental_data_dimensions(path_to_raw_data: str) \
    -> tuple[int, int, int, int]:
    """Get the dimensions of the raw elemental data.
    
    :param path_to_raw_data: Path to the raw data file in the server.
    :param config_path: Path to the backend config file
    :return: 4-tuple of the dimensions of the raw elemental data and the header size (in bytes).
    Tuple is as follows (width, height, channels, header size)
    """
    header_size: int = 0
    dimensions: list[int] = []    # Dimensions of the dataset
    try:
        with open(abspath(path_to_raw_data), 'rb') as file:
            # Read the first line and ignore it (doesn't include important data)
            file.readline()

            # Read the second line
            dimensions_str: str = file.readline().decode('ascii').strip().split()
            
            # Parse the second line into the dimensions
            dimensions = [int(dim) for dim in dimensions_str]

            # Save the size of the header
            header_size = file.tell()
    except Exception as e:
        LOG.error(f"Could not read elemental data file: {str(e)}")
        return ()

    return (*dimensions, header_size)


def get_raw_elemental_data(config_path: str = "config/backend.yml") -> np.ndarray:
    """Get the raw elemental data.
    
    :param config_path: Path to the backend config file
    :return: 3-dimensional numpy array containing the raw elemental data. First 2 dimensions
    are x, y coordinates, last dimension is for channels i.e. elements.
    """

    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return np.empty(0)
    filename_elemental: str = '196_1989_M6_elemental_datacube_1069_1187_rotated_inverted.dms'

    # get the path to the file in the server
    path_to_file: str = join(Path(backend_config['uploads-folder']), filename_elemental)

    # data dimensions
    try:
        (w, h, c, header_size) = get_raw_elemental_data_dimensions(path_to_file)
    except Exception as e:
        LOG.error(f"Could not read elemental data file: {str(e)}")
        return np.empty(0)

    # convert it into a numpy array
    try:
        raw_data: np.ndarray = np.fromfile(path_to_file, offset=header_size, count=w*h*c, dtype=np.float32)
    except Exception as e:
        LOG.error(f"Could not read elemental data file: {str(e)}")
        return np.empty(0)

    # normalize data
    (raw_data_min, raw_data_max) = raw_data.min(), raw_data.max()
    normalized_data: np.ndarray = (raw_data - raw_data_min) / (raw_data_max - raw_data_min)

    # obtain image of elemental abundance at every pixel of elemental image
    image_values: np.ndarray = np.rint(normalized_data * 255).astype(np.uint8)
    image_cube: np.ndarray = np.reshape(image_values, (c, h, w))

    return image_cube


def get_element_names(config_path: str = "config/backend.yml") -> list[str]:
    """Get the names of the elements present in the painting.

    :param config_path: Path to the backend config file
    :return: List of the names of the elements.
    """

    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return []

    filename_elemental: str = '196_1989_M6_elemental_datacube_1069_1187_rotated_inverted.dms'

    # get the path to the file in the server
    path_to_file: str = join(Path(backend_config['uploads-folder']), filename_elemental)

    # data dimensions
    try:
        (w, h, c, header_size) = get_raw_elemental_data_dimensions(path_to_file)
    except Exception as e:
        LOG.error(f"Could not read elemental data file: {str(e)}")
        return np.empty(0)

    # get the names of the elements
    names: list[str] = []
    try:
        with open(abspath(path_to_file), 'r') as file:
            file.seek(header_size + 1 + w * h * c * 4)
            for _ in range(c):
                current: str = file.readline().rstrip().replace(" ", "")
                # shorten names for continuum and chi maps, to save space in the plot
                if current == "Continuum":
                    current = "cont."
                elif current == "chisq":
                    current = "chi"
                names.append(current)
    except Exception as e:
        LOG.error(f"Could not read elemental data file: {str(e)}")
        return []

    return names


def get_element_averages(config_path: str = "config/backend.yml") -> list[dict[str, str | float]]:
    """Get the names and averages of the elements present in the painting.

    :param config_path: path to the backend config file
    :return: List of the names and average composition of the elements.
    """

    image_cube: np.ndarray = get_raw_elemental_data(config_path)
    names: list[str] = get_element_names(config_path)

    if image_cube.size == 0 or names == []:
        LOG.error(f"Couldn't parse elemental image cube or list of names")
        return []

    averages: np.ndarray = np.mean(image_cube, axis=(1, 2))
    
    composition: list[dict[str,  str | float]] = \
        [{"name": names[i], "average": averages[i]} for i in range(averages.size)]

    return composition
