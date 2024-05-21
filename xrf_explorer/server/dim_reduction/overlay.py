import logging 

from os.path import join
from pathlib import Path

import numpy as np
import matplotlib
import matplotlib.pyplot as plt

from xrf_explorer.server.file_system.config_handler import load_yml
from xrf_explorer.server.dim_reduction.general import valid_element, get_elemental_data_cube, get_registered_painting_image

matplotlib.use('Agg')

LOG: logging.Logger = logging.getLogger(__name__)

OVERLAY_IMAGE: list[str] = ['rgb', 'uv', 'xray']


def create_embedding_image(overlay_type: str, config_path: str = "config/backend.yml") -> bool:
    """Create the embedding image from the embedding.

    :param overlay_type: The type of overlay to create. Can be 'rgb', 'uv', 'xray' or an element number.
    :param config_path: Path to the backend config file
    :return: True if the embedding was successfully generated. Otherwise False.
    """

    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        return False
    dr_folder: dict = backend_config['dim-reduction']['folder']

    # Load the file embedding.npy
    try:
        indices: np.ndarray = np.load(Path(backend_config['temp-folder'], dr_folder, 'indices.npy'))
        embedding: np.ndarray = np.load(Path(backend_config['temp-folder'], dr_folder, 'embedded_data.npy'))
    except OSError as e:
        LOG.error(f"Failed to load indices and/or embedding data. Error: {e}")
        return False

    # Create the overlay
    overlay: np.ndarray

    if overlay_type in OVERLAY_IMAGE:
        overlay = create_image_overlay(overlay_type, indices)
    else:
        # Show element overlay
        # Get the element
        element: int = int(overlay_type)

        # Get elemental data cube
        data_cube: np.ndarray | None = get_elemental_data_cube()

        if data_cube is None:
            return False

        # Verify valid element
        if not valid_element(element, data_cube):
            return False

        # Create the overlay
        embedding, overlay = create_element_overlay(element, indices, data_cube, embedding)

    # Create the plot
    LOG.info("Creating embedding image...")
    create_image(embedding, overlay, Path(backend_config['temp-folder'], dr_folder))
    LOG.info("Created embedding image successfully")

    return True


def create_image_overlay(overlay_type: str, indices: np.ndarray) -> np.ndarray:
    """ Gets the pixels out of the image at the given indices.

    :param overlay_type: The type of overlay to create.
    :param indices: The indices to get the pixels from.
    :return: The pixels at the given indices of the image.
    """

    # Get the pixels in the picture at the given path
    overlay_data: np.ndarray = get_registered_painting_image(overlay_type)

    # Get the pixels at the given indices
    overlay: np.ndarray = overlay_data[indices[:, 0], indices[:, 1]]
    
    # Normalize the pixels values to be in the range [0, 1]
    overlay = overlay.astype(float) / 255.0

    return overlay


def create_element_overlay(
        element: np.ndarray, indices: np.ndarray, 
        data_cube: np.ndarray, embedding: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Creates an intensity overlay of the given element.
    
    :param element: The element to create the overlay for.
    :param indices: The indices of the data to create the overlay for.
    :param data: The data to create the overlay from.
    :param embedding: The embedding data.
    :return: The reordered embedding and overlay of the given element.
    """

    # Get elemental overlay
    overlay: np.ndarray = data_cube[indices[:, 0], indices[:, 1], element]

    # We want to first show low intensities and then high intensities
    # This is because we are interested in high intensity regions
    sorted_indices: np.ndarray = np.argsort(overlay)
    sorted_embedding: np.ndarray = embedding[sorted_indices]
    sorted_overlay: np.ndarray = overlay[sorted_indices]

    return sorted_embedding, sorted_overlay


def create_image(embedding: np.ndarray, overlay: np.ndarray, path: Path) -> None:
    """Creates the image of the embedding with the overlay and saves it to the given path.
    
    :param embedding: The embedding data.
    :param overlay: The overlay data.
    :param path: The path to save the image.
    """

    # Create the plot
    fig = plt.figure(figsize=(15, 12))

    plt.axis('off')
    fig.patch.set_facecolor('black')

    plt.scatter(embedding[:, 0], embedding[:, 1], c=overlay, alpha=0.5, s=15)

    plt.savefig(join(path, 'embedding.png'), bbox_inches='tight', transparent=True)


def get_embedding_image(overlay_type: str) -> str:
    """Create the embedding image based on the given arguments.

    :param overlay_type: The type of overlay to create.
    :return: String path to the embedding image. If an error occured
    an empty string is returned.
    """

    LOG.info("Creating embedding image...")

    # Create the embedding image
    if not create_embedding_image(overlay_type):
        LOG.error("Failed to create DR embedding image")
        return ""
    
    # Return the embedding
    LOG.info("Created embedding image successfully")
    return "server/temp/dim_reduction/embedding.png" # TODO: Fix this path
