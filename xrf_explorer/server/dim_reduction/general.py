import logging 

from os.path import isfile
from pathlib import Path

import numpy as np
import imageio.v3 as imageio

from xrf_explorer.server.file_system.config_handler import load_yml

LOG: logging.Logger = logging.getLogger(__name__)


def valid_element(element: int, data_cube: np.ndarray) -> bool:
    # verify valid element
    total_number_of_elements: int = data_cube.shape[2]

    if element < 0 or element >= total_number_of_elements:
        LOG.error(f"Invalid element: {element}")
        return False
    
    return True


def get_elemental_data_cube(config_path: str = "config/backend.yml") -> np.ndarray | None:
    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        LOG.error("Failed to compute DR embedding")
        return None
    
    # path to elemental data cube
    data_cube_path: Path = Path(backend_config['uploads-folder'], 'test_cube.npy')

    # check if data cube exists
    if not isfile(data_cube_path):
        LOG.error(f"Data cube not found: {data_cube_path}")
        return None
    
    # load data cube
    elemental_data_cube: np.ndarray = np.load(data_cube_path)
    LOG.info(f"Loaded data cube from: {data_cube_path}")

    return elemental_data_cube


def get_registered_painting_image(type: str, config_path: str = "config/backend.yml") -> np.ndarray:
    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        LOG.error("Failed to compute DR embedding")
        return False
    
    # path to the painting image
    path_to_image: Path = Path(backend_config['uploads-folder'], 'test overlays', f'{type}.png')

    # load pixels of image
    pixels_of_image: np.ndarray = imageio.imread(path_to_image)

    return pixels_of_image
