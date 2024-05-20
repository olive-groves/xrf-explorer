import logging
import numpy as np

from os.path import join, abspath
from pathlib import Path

from xrf_explorer.server.file_system.config_handler import load_yml

LOG: logging.Logger = logging.getLogger(__name__)

def get_raw_elemental_data(config_path: str = "config/backend.yml") -> np.ndarray:
    """Get the raw elemental data.
    
    :param config_path: path to the backend config file
    :return: 3-dimensional numpy array containing the raw elemental data.
    """

    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return np.ndarray([])

    filename_elemental = '196_1989_M6_elemental_datacube_1069_1187_rotated_inverted.dms'

    # get the path to the file in the server
    path_to_file: str = join(Path(backend_config['uploads-folder']), filename_elemental)

    # data dimensions
    w = 1069
    h = 1187
    c = 26
    header_size = 48 # in bytes

    # convert it into a numpy array
    raw_data: np.ndarray = np.fromfile(path_to_file, offset=header_size, count=w*h*c, dtype=np.float32)

    # normalize data
    (min, max) = raw_data.min(), raw_data.max()
    normalized_data: np.ndarray = (raw_data - min) / (max - min)

    # obtain image cube for each element
    image_values: np.ndarray = np.rint(normalized_data * 255).astype(np.uint8)
    image_cube: np.ndarray = np.reshape(image_values, (c, h, w))

    return image_cube

def get_element_names(config_path: str = "config/backend.yml") -> list[str]:
    """Get the names of the elements present in the painting.

    :param config_path: path to the backend config file
    :return: List of the names of the elements.
    """

    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return []

    filename_elemental = '196_1989_M6_elemental_datacube_1069_1187_rotated_inverted.dms'

    # data dimensions
    w = 1069
    h = 1187
    c = 26
    header_size = 48 # in bytes
    
    # get the path to the file in the server
    path_to_file: str = join(Path(backend_config['uploads-folder']), filename_elemental)

    # get the names of the elements
    names: list[str] = []
    with open(abspath(path_to_file), 'r') as file:
        file.seek(header_size + 1 + w * h * c * 4)
        for _ in range(c):
            current = file.readline().rstrip().replace(" ", "")
            if current == "Continuum":
                current = "cont."
            elif current == "chisq":
                current = "chi"
            names.append(current)

    return names

def get_element_averages(config_path: str = "config/backend.yml") -> dict[str, str | float]:
    """Get the names and averages of the elements present in the painting.

    :param config_path: path to the backend config file
    :return: Dictionary of the names and average composition of the elements.
    """

    image_cube: np.ndarray = get_raw_elemental_data(config_path)
    averages: np.ndarray = np.mean(image_cube, axis=(1,2))
    names: list[str] = get_element_names(config_path)
    
    composition: list[dict[str,  str | float]] = [{ "name": names[i], "average": averages[i]} for i in range(averages.size)]

    return composition
