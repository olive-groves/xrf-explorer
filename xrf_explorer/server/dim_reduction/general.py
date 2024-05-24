import logging 

from os.path import isfile, abspath
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
        return np.empty(0)
    
    # path to the painting image
    path_to_image: Path = Path(backend_config['uploads-folder'], 'test overlays', f'{type}.png')

    # load pixels of image
    pixels_of_image: np.ndarray = imageio.imread(path_to_image)

    return pixels_of_image


def get_image_of_indices_to_embedding(config_path: str = "config/backend.yml"):
    """Creates the image for lasso selection that decodes to which points in the embedding
    the pixels of the elemental data cube are mapped. Uses the current embedding and indices
    to create the image.

    :param config_path: Path to the backend config file
    :return: True if the image was created successfully, otherwise False.
    """

    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        return False

    # Load the elemental data cube
    elemental_cube: np.ndarray | None = get_elemental_data_cube(config_path=config_path)
    if elemental_cube is None:
        return False

    # Load data indices and embedded data
    dr_folder: str = backend_config['dim-reduction']['folder']

    # Load the file embedding.npy
    try:
        indices: np.ndarray = np.load(Path(abspath(dr_folder), 'indices.npy'))
        embedding: np.ndarray = np.load(Path(abspath(dr_folder), 'embedded_data.npy'))
    except OSError as e:
        LOG.error(f"Failed to load indices and/or embedding data. Error: {e}")
        return False

    # Get min and max values
    xmin, ymin = np.min(embedding, axis=0)
    xmax, ymax = np.max(embedding, axis=0)

    # Normalize values to be in the range [0, 255]
    embedding[:, 0] = np.interp(embedding[:, 0], (xmin, xmax), (0, +255))
    embedding[:, 1] = np.interp(embedding[:, 1], (ymin, ymax), (0, +255))

    # Initialize new image
    newimage = np.zeros((elemental_cube.shape[0], elemental_cube.shape[1], 3), dtype=np.uint8)
    
    # Fill pixels
    newimage[indices[:, 0], indices[:, 1], 0] = embedding[:, 0]
    newimage[indices[:, 0], indices[:, 1], 1] = embedding[:, 1]
    newimage[indices[:, 0], indices[:, 1], 2] = 255

    # Create and save the image
    imageio.imwrite(Path(abspath(dr_folder), 'image_index_to_embedding.npy'), newimage)

    return True
