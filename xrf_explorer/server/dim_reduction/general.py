import logging

from os import makedirs
from os.path import join, isdir, isfile

import numpy as np

from cv2 import imwrite
from scipy.interpolate import NearestNDInterpolator

from xrf_explorer.server.file_system import get_config, get_path_to_generated_folder
from xrf_explorer.server.file_system.cubes import get_elemental_data_cube

LOG: logging.Logger = logging.getLogger(__name__)

MAPPING_IMAGE_NAME: str = 'image_index_to_embedding.png'


def valid_element(element: int, data_cube: np.ndarray) -> bool:
    """Verifies whether the given element is valid for the given data cube.
    
    :param element: The element to verify
    :param data_cube: The data cube to verify the element for
    :return: True if the element is valid, otherwise False
    """

    # verify valid element
    total_number_of_elements: int = data_cube.shape[0]

    if element < 0 or element >= total_number_of_elements:
        LOG.error(f"Invalid element: {element}")
        return False

    return True


def get_path_to_dr_folder(data_source: str) -> str:
    """Get the path to the dimensionality reduction folder for a given datasource. If it does not exist the folder is
    created.
    
    :param data_source: The name of the datasource
    :return: The path to the dimensionality reduction folder for the given datasource
    """

    # load backend config
    backend_config: dict = get_config()
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return ""

    # Get path to generated folder of the data source
    path_to_generated_folder: str = get_path_to_generated_folder(data_source)
    if not path_to_generated_folder:
        return ""

    # Path to the dimensionality reduction folder
    path_to_dr_folder: str = join(path_to_generated_folder, backend_config['dim-reduction']['folder-name'])

    # Check if the dimensionality reduction folder exists, otherwise create it
    if not isdir(path_to_dr_folder):
        makedirs(path_to_dr_folder)
        LOG.info(f"Created directory {path_to_dr_folder}.")

    LOG.info(f"Dimensionality reduction folder {data_source} found.")
    return path_to_dr_folder


def create_image_of_indices_to_embedding(data_source: str) -> bool:
    """Creates the image for polygon selection that decodes to which points in the embedding the pixels of the elemental
    data cube are mapped. Uses the current embedding and indices to create the image.

    :param data_source: Name of the data source
    :return: True if the image was created successfully, otherwise False
    """

    dr_folder: str = get_path_to_dr_folder(data_source) # Get the path to the dimensionality reduction folder
    elemental_cube: np.ndarray | None = get_elemental_data_cube(data_source) # Load the elemental data cube
    
    # Check if the folder and the elemental data cube are loaded
    if not dr_folder or elemental_cube is None:
        return False

    # Load the file embedding.npy
    try:
        indices: np.ndarray = np.load(join(dr_folder, 'indices.npy'))
        all_indices: np.ndarray = np.load(join(dr_folder, 'all_indices.npy'))
        embedding: np.ndarray = np.load(join(dr_folder, 'embedded_data.npy'))
    except OSError as e:
        LOG.error(f"Failed to load indices and/or embedding data. Error: {e}")
        return False

    # Get min and max values
    xmin, ymin = np.min(embedding, axis=0)
    xmax, ymax = np.max(embedding, axis=0)

    # Normalize values to be in the range [0, 255]
    embedding[:, 0] = np.interp(embedding[:, 0], (xmin, xmax), (0, +255))
    embedding[:, 1] = np.interp(embedding[:, 1], (ymin, ymax), (0, +255))

    LOG.info(f"Creating the interpolator with the data of size: {indices.shape[0]}")
    interp = NearestNDInterpolator(elemental_cube[:, indices[:, 0], indices[:, 1]].T, embedding)

    LOG.info(f"Interpolating the data of size: {all_indices.shape[0]}")
    interpolated = interp(elemental_cube[:, all_indices[:, 0], all_indices[:, 1]].T)

    # Initialize new image
    LOG.info("Creating the mapping image")
    newimage = np.zeros((elemental_cube.shape[1], elemental_cube.shape[2], 3), dtype=np.uint8)

    # Fill pixels (in BGR format)
    newimage[all_indices[:, 0], all_indices[:, 1], 0] = 255
    newimage[all_indices[:, 0], all_indices[:, 1], 1] = interpolated[:, 1]
    newimage[all_indices[:, 0], all_indices[:, 1], 2] = interpolated[:, 0]

    # Create and save the image
    path_image: str = join(dr_folder, MAPPING_IMAGE_NAME)
    imwrite(path_image, newimage)

    LOG.info("Created DR image index to embedding.")

    return True


def get_image_of_indices_to_embedding(data_source: str) -> str:
    """Returns the path to the image that maps the indices of the elemental data cube to the embedding.

    :param data_source: Name of the data source
    :return: Path to the image. If the image is not found, an empty string is returned
    """
    # Get the path to the dimensionality reduction folder
    dr_folder: str = get_path_to_dr_folder(data_source)
    if not dr_folder:
        return ""

    # Check if the image exists
    file_path: str = join(dr_folder, MAPPING_IMAGE_NAME)
    if not isfile(file_path):
        LOG.error(f"File {MAPPING_IMAGE_NAME} not found.")
        return ""

    return join(dr_folder, MAPPING_IMAGE_NAME)
