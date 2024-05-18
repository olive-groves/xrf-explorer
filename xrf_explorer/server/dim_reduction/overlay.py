import logging 

from os.path import join
from pathlib import Path

import numpy as np
import imageio.v3 as imageio

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from xrf_explorer.server.file_system.config_handler import load_yml

LOG: logging.Logger = logging.getLogger(__name__)

OVERLAY_ARGS: list[str] = ['type']
OVERLAY_IMAGE: list[str] = ['rgb', 'uv', 'xray']


def create_embedding_image(args: dict[str, str], config_path: str = "config/backend.yml") -> bool:
    """Create the embedding image from the embedding.

    :param args: Arguments for generating the overlay. Should at least contain the type.
    :param config_path: Path to the backend config file
    :return: True if the embedding was successfully generated. Otherwise False.
    """

    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        return False
    dr_folder = backend_config['dim-reduction']['folder']

    # Get the overlay type
    overlay_type = args['type']

    # Load the file embedding.npy
    try:
        indices = np.load(Path(backend_config['temp-folder'], dr_folder, 'indices.npy'))
        embedding = np.load(Path(backend_config['temp-folder'], dr_folder, 'embedded_data.npy'))
    except:
        LOG.error("Failed to load embedding data")
        return False

    if overlay_type in OVERLAY_IMAGE:
        # Show image overlay TODO: change to actual image
        overlay = create_image_overlay(indices, f'{backend_config['temp-folder']}/test overlays/{overlay_type}.png')
    else:
        # Show element overlay
        # Get the element
        element = int(overlay_type)

        # Get elemental data cube
        data = np.load(Path(backend_config['uploads-folder'], 'test_cube.npy'))

        # Verify valid element
        if element < 0 or element >= data.shape[2]:
            LOG.error(f"Invalid element: {element}")
            return False

        # Create the overlay
        embedding, overlay = create_element_overlay(element, indices, data, embedding)

    # Create the plot
    create_image(embedding, overlay, Path(backend_config['temp-folder'], dr_folder))

    return True


def create_image_overlay(indices, path: Path | str):
    """ Gets the pixels out of the image at the given indices.

    :param indices: The indices to get the pixels from.
    :param path: The path to the image.
    :return: The pixels at the given indices of the image.
    """

    overlay_data = imageio.imread(path)
    overlay = overlay_data[indices[:, 0], indices[:, 1]]
    overlay = overlay.astype(float) / 255.0

    return overlay


def create_element_overlay(element, indices, data, embedding):
    """Creates an intensity overlay of the given element.
    
    :param element: The element to create the overlay for.
    :param indices: The indices of the data to create the overlay for.
    :param data: The data to create the overlay from.
    :return: The reorderd embedding and overlay of the given element.
    """

    # Get elemental overlay
    overlay = data[indices[:, 0], indices[:, 1], element]

    # We want to first show low intensities and then high intensities
    # This is because we are interested in high intensity regions
    sorted_ind = np.argsort(overlay)
    embedding = embedding[sorted_ind]
    overlay = overlay[sorted_ind]

    return embedding, overlay


def create_image(embedding, overlay, path: Path) -> None:
    """Creates the image of the embedding with the overlay and saves it to the given path.
    
    :param embedding: The embedding data.
    :param overlay: The overlay data.
    :param path: The path to save the image.
    """

    # Create the plot
    fig = plt.figure(figsize=(15, 12))

    plt.axis('off')
    fig.patch.set_facecolor(('black'))

    plt.scatter(embedding[:, 0], embedding[:, 1], c=overlay, alpha=0.5, s=15)

    plt.savefig(join(path, 'embedding.png'), bbox_inches='tight', transparent=True)


def get_embedding_image(args: dict[str, str]) -> str:
    """Create the embedding image based on the given arguments.

    :param args: A dictionary containing the arguments for the overlay.
    :return: Response containing the embedding image if successful. Otherwise a tuple containing the error message and status code.
    """

    LOG.info("Creating embedding image...")

    # Create the embedding image
    if not create_embedding_image({key: args[key] for key in OVERLAY_ARGS if key in args.keys()}):
        LOG.error("Failed to create DR embedding image")
        return ""
    
    # Return the embedding
    LOG.info("Created embedding image successfully")
    return "server/temp/dim_reduction/embedding.png" # TODO: Fix this path
