import logging 

from os import remove
from os.path import join
from pathlib import Path

import numpy as np
from cv2 import imread

from xrf_explorer.server.file_system.config_handler import load_yml
from xrf_explorer.server.file_system.contextual_images import get_contextual_image_path
from xrf_explorer.server.file_system.file_access import get_elemental_cube_path
from xrf_explorer.server.image_register import register_image_to_data_cube

LOG: logging.Logger = logging.getLogger(__name__)


def valid_element(element: int, data_cube: np.ndarray) -> bool:
    """Verifies whether the given element is valid for the given data cube.
    
    :param element: The element to verify.
    :param data_cube: The data cube to verify the element for.
    :return: True if the element is valid, otherwise False.
    """

    # verify valid element
    total_number_of_elements: int = data_cube.shape[0]

    if element < 0 or element >= total_number_of_elements:
        LOG.error(f"Invalid element: {element}")
        return False
    
    return True


def get_registered_image(data_source: str, image_name: str, config_path: str = "config/backend.yml") -> np.ndarray:
    """Get image registered to given data source.
    
    :param data_source: Name of the data source to get the registered image for.
    :param image_name: Name of the image to get the registered image for.
    :param config_path: Path to the backend config file
    :return: Pixels of the registered image if successful, otherwise empty array.
    """

    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        return np.empty(0)

    # Get the path to the image
    image_path: str | None = get_contextual_image_path(data_source, image_name, config_path=config_path)
    if image_path is None:
        return np.empty(0)
    
    # Get the path to the elemental data cube
    cube_path: str = get_elemental_cube_path(data_source, config_path=config_path)
    if not cube_path:
        return np.empty(0)
    
    # Register the image to the data cube
    temp_path: str = join(backend_config['temp-folder'], "registered_" + Path(image_path).name)
    registered_image: bool = register_image_to_data_cube(cube_path, image_path, temp_path)
    if not registered_image:
        return np.empty(0)

    # load pixels of image
    pixels_of_image: np.ndarray = imread(temp_path)

    # delete temp file
    remove(temp_path)

    return pixels_of_image
