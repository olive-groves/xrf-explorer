import logging 

from os.path import join, abspath

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from cv2 import cvtColor, COLOR_BGR2RGB
from cv2.typing import MatLike

from xrf_explorer.server.file_system.cubes.elemental import get_elemental_data_cube
from xrf_explorer.server.file_system.workspace.file_access import get_elemental_cube_path
from xrf_explorer.server.process.image_register import get_image_registered_to_data_cube

from .general import valid_element, get_path_to_dr_folder

matplotlib.use('Agg')

LOG: logging.Logger = logging.getLogger(__name__)


def create_embedding_image(data_source: str, overlay_type: str) -> str:
    """Creates the embedding image from the embedding.

    :param data_source: Name of the data source to create the embedding image for.
    :param overlay_type: The type of overlay to create. Can be the name of image prefixed by contextual_ or an element number prefixed by elemental_.
    :return: Path to created embedding image is successful, otherwise empty string.
    """

    LOG.info("Creating embedding image...")

    # Get the path to the DR folder
    dr_folder: str = get_path_to_dr_folder(data_source)
    if not dr_folder:
        return ""

    # Load the file embedding.npy
    try:
        indices: np.ndarray = np.load(join(abspath(dr_folder), 'indices.npy'))
        embedding: np.ndarray = np.load(join(abspath(dr_folder), 'embedded_data.npy'))
    except OSError as e:
        LOG.error(f"Failed to load indices and/or embedding data. Error: {e}")
        return ""

    # Get the path to the elemental data cube
    cube_path: str = get_elemental_cube_path(data_source)
    if not cube_path:
        return ""

    # Create the overlay
    overlay: np.ndarray

    if overlay_type.startswith("contextual_"):
        # Get image type
        image_type: str = overlay_type.removeprefix("contextual_")

        # Get the pixels of registered image
        registered_image: MatLike | None = get_image_registered_to_data_cube(data_source, image_type)
        if registered_image is None:
            return ""
        
        # Convert BGR to RGB
        registered_rgb_image: np.ndarray = cvtColor(registered_image, COLOR_BGR2RGB)

        # Create the overlay
        overlay = create_image_overlay(registered_rgb_image, indices)
    elif overlay_type.startswith("elemental_"):
        # Show element overlay
        # Get the element
        element: int = int(overlay_type.removeprefix("elemental_"))

        # Get elemental data cube
        data_cube: np.ndarray = get_elemental_data_cube(cube_path)
        if len(data_cube) == 0:
            return ""

        # Verify valid element
        if not valid_element(element, data_cube):
            return ""

        # Create the overlay
        embedding, overlay = create_element_overlay(element, indices, data_cube, embedding)
    else:
        LOG.error(f"Invalid overlay type: {overlay_type}")
        return ""

    LOG.info("Created overlay successfully")

    # Create the plot
    LOG.info("Creating embedding image...")
    path_to_image = plot_embedding_with_overlay(embedding, overlay, dr_folder)
    LOG.info("Created embedding image successfully")

    return path_to_image


def create_image_overlay(registered_image: np.ndarray, indices: np.ndarray) -> np.ndarray:
    """Creates the overlay based on the given image type. This is done by getting the pixels out of the image at the
    given indices.

    :param registered_image: The pixels of the registered image to create the overlay from.
    :param indices: The indices to get the pixels from.
    :return: The normalized pixels at the given indices of the image.
    """

    # Get the pixels at the given indices
    overlay: np.ndarray = registered_image[indices[:, 0], indices[:, 1]]
    
    # Normalize the pixels values to be in the range [0, 1]
    overlay = overlay.astype(float) / 255.0

    return overlay


def create_element_overlay(
        element: int, indices: np.ndarray,
        data_cube: np.ndarray, embedding: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Creates an intensity overlay of the given element.

    :param element: The element to create the overlay for.
    :param indices: The indices of the data to create the overlay for.
    :param data_cube: The data to create the overlay from.
    :param embedding: The embedding data.
    :return: The reordered embedding and overlay of the given element.
    """

    # Get elemental overlay
    overlay: np.ndarray = data_cube[element, indices[:, 0], indices[:, 1]]

    # We want to first show low intensities and then high intensities
    # This is because we are interested in high intensity regions
    sorted_indices: np.ndarray = np.argsort(overlay)
    sorted_embedding: np.ndarray = embedding[sorted_indices]
    sorted_overlay: np.ndarray = overlay[sorted_indices]

    return sorted_embedding, sorted_overlay


def plot_embedding_with_overlay(embedding: np.ndarray, overlay: np.ndarray, path: str) -> str:
    """Makes the image of the given embedding with the given overlay and saves it to the given path.
    
    :param embedding: The embedding data.
    :param overlay: The overlay data.
    :param path: The path to save the image.
    :return: Path to the created image.
    """

    # Create the plot
    fig = plt.figure(figsize=(15, 12))

    plt.axis('off')
    fig.patch.set_facecolor('black')
    
    # Get the minimum and maximum values of the embedding (values can possibly be NaN)
    xmin, xmax = np.nanmin(embedding[:, 0]), np.nanmax(embedding[:, 0])
    ymin, ymax = np.nanmin(embedding[:, 1]), np.nanmax(embedding[:, 1])

    # Check if all min and max are not NaN
    if np.isnan([xmin, xmax, ymin, ymax]).any():
        LOG.error("Failed to create embedding image. The embedding data contains NaN values.")
        return ""

    # Set limits to match the data
    plt.xlim(xmin, xmax)
    plt.ylim(ymin, ymax)

    plt.scatter(embedding[:, 0], embedding[:, 1], c=overlay, alpha=0.5, s=15)

    # Save the plot
    image_path = join(path, 'embedding.png')

    plt.savefig(image_path, bbox_inches='tight', transparent=True)

    return image_path
