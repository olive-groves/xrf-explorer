import logging 

from os import remove, makedirs
from os.path import isdir, join
from pathlib import Path

import numpy as np
from cv2 import imread, imwrite

from xrf_explorer.server.file_system.config_handler import get_config
from xrf_explorer.server.file_system.contextual_images import get_contextual_image_path
from xrf_explorer.server.image_register import register_image_to_data_cube
from xrf_explorer.server.file_system import get_elemental_data_cube, get_elemental_cube_path

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


def get_registered_image(data_source: str, image_name: str) -> np.ndarray:
    """Get image registered to given data source.
    
    :param data_source: Name of the data source to get the registered image for.
    :param image_name: Name of the image to get the registered image for.
    :return: Pixels of the registered image if successful, otherwise empty array.
    """

    # load backend config
    backend_config: dict = get_config()
    if not backend_config:  # config is empty
        return np.empty(0)

    # Get the path to the image
    image_path: str | None = get_contextual_image_path(data_source, image_name)
    if image_path is None:
        return np.empty(0)
    
    # Get the path to the elemental data cube
    cube_path: str = get_elemental_cube_path(data_source)
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


def get_path_to_dr_folder(data_source: str, config_path: str = "config/backend.yml") -> str:
    """Get the path to the dimensionality reduction folder for a given datasource. If it does not exists the folder is created.
    
    :param data_source: The name of the datasource
    :param config_path: The path to the backend config file
    :return: The path to the dimensionality reduction folder for the given datasource.
    """

    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return ""

    # Path to the data source folder
    path_to_data_source: str = join(
        backend_config['uploads-folder'], data_source
    )

    # Check if the datasource exists
    if not isdir(path_to_data_source):
        LOG.error(f"Datasource {data_source} not found.")
        return ""
    
    path_to_generated_folder: str = join(path_to_data_source, backend_config['generated-folder-name'])
    if not isdir(path_to_generated_folder):
        makedirs(path_to_generated_folder)
        LOG.info(f"Created directory {path_to_generated_folder}.")

    # Path to the dimensionality reduction folder
    path_to_dr_folder: str = join(path_to_generated_folder, backend_config['dim-reduction']['folder-name'])

    # Check if the dimensionality reduction folder exists
    if not isdir(path_to_data_source):
        makedirs(path_to_data_source)
        LOG.info(f"Created directory {path_to_data_source}.")

    LOG.info(f"Dimensionality reduction folder {data_source} found.")
    return path_to_dr_folder


def get_image_of_indices_to_embedding(data_source: str, config_path: str = "config/backend.yml") -> str:
    """Creates the image for lasso selection that decodes to which points in the embedding
    the pixels of the elemental data cube are mapped. Uses the current embedding and indices
    to create the image.

    :param data_source: Name of the data source.
    :param config_path: Path to the backend config file
    :return: True if the image was created successfully, otherwise False.
    """
    # Get the path to the dimensionality reduction folder
    dr_folder: str = get_path_to_dr_folder(data_source, config_path)
    if not dr_folder:
        return ""

    # Load the elemental data cube
    path_to_cube = get_elemental_cube_path(data_source, config_path=config_path)
    elemental_cube: np.ndarray | None = get_elemental_data_cube(path_to_cube)
    if elemental_cube is None:
        return ""

    # Load the file embedding.npy
    try:
        indices: np.ndarray = np.load(join(dr_folder, 'indices.npy'))
        embedding: np.ndarray = np.load(join(dr_folder, 'embedded_data.npy'))
    except OSError as e:
        LOG.error(f"Failed to load indices and/or embedding data. Error: {e}")
        return ""

    # Get min and max values
    xmin, ymin = np.min(embedding, axis=0)
    xmax, ymax = np.max(embedding, axis=0)

    # Normalize values to be in the range [0, 255]
    embedding[:, 0] = np.interp(embedding[:, 0], (xmin, xmax), (0, +255))
    embedding[:, 1] = np.interp(embedding[:, 1], (ymin, ymax), (0, +255))

    # Initialize new image
    newimage = np.zeros((elemental_cube.shape[1], elemental_cube.shape[2], 3), dtype=np.uint8)
    
    # Fill pixels
    newimage[indices[:, 0], indices[:, 1], 0] = embedding[:, 0]
    newimage[indices[:, 0], indices[:, 1], 1] = embedding[:, 1]
    newimage[indices[:, 0], indices[:, 1], 2] = 255

    # Create and save the image
    path_image: str = join(dr_folder, 'image_index_to_embedding.png')
    imwrite(path_image, newimage)

    LOG.info(f"Created DR image index to embedding.")

    return path_image
