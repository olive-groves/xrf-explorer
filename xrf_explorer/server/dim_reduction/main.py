import logging 

from pathlib import Path

import numpy as np
import imageio.v3 as imageio

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from xrf_explorer.server.file_system.config_handler import load_yml

LOG: logging.Logger = logging.getLogger(__name__)

DR_ARGS = ['element', 'threshold', 'n_neighbors', 'min_dist', 'n_components', 'metric']
OVERLAY_ARGS = ['type']
OVERLAY_IMAGE = ['rgb', 'uv', 'xray']


def apply_umap(data, parms: dict[str, str]):
    """Apply UMAP to the given data with the given parameters.

    :param data: Data to apply UMAP to.
    :param parms: A dictionary containing the paramets for UMAP.
    :return: The embedded data.
    """

    from umap import UMAP

    return UMAP(
        n_neighbors=int(parms['n_neighbors']),
        min_dist=float(parms['min_dist']),
        n_components=int(parms['n_components']), 
        metric= parms['metric']
    ).fit_transform(data)


def generate_embedding(args: dict[str, str], config_path: str = "config/backend.yml") -> bool:
    """Generate the embedding of the elemental data cube.

    :param args: Arguments for generating the embedding.
    :param config_path: Path to the backend config file
    :return: True if the embedding was successfully generated. Otherwise False.
    """

    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        return False
    
    # get default dim reduction config
    dr_config: dict = backend_config['dim-reduction']
    dr_config.update(args)

    # Constants
    element = int(dr_config['element'])
    threshold = int(dr_config['threshold'])

    # get data cube
    data_cube_path: Path = Path(backend_config['uploads-folder'], 'test_cube.npy') # TODO change this to the actual data cube
    data = np.load(data_cube_path)

    # check if element is valid
    if element < 0 or element >= data.shape[2]:
        LOG.error(f"Invalid element: {element}")
        return False

    # filter data
    indices = np.argwhere(data[:, :, element] >= threshold)

    # get filtered data
    spectra = data[indices[:, 0], indices[:, 1], :]

    # compute embedding
    LOG.info(f"Generating embedding with: el {element}, tr {threshold}, size {spectra.shape}")
    try:
        embedded_data = apply_umap(spectra, dr_config)
    except ValueError as e:
        LOG.error(f"Failed to compute embedding: {e}")
        return False

    # save indices and embedded data
    np.save(Path(backend_config['temp-folder'], dr_config['folder'], 'indices.npy'), indices)
    np.save(Path(backend_config['temp-folder'], dr_config['folder'], 'embedded_data.npy'), embedded_data)

    return True


def create_embedding_image(args: dict[str, str], config_path: str = "config/backend.yml") -> bool:
    """Create the embedding image from the embedding.

    :param args: Arguments for generating the overlay.
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
        overlay_data = imageio.imread(f'{backend_config['temp-folder']}/test overlays/{overlay_type}.png')
        overlay = overlay_data[indices[:, 0], indices[:, 1]]
        overlay = overlay.astype(float) / 255.0
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

        # Get elemental overlay
        overlay = data[indices[:, 0], indices[:, 1], element]

        # We want to first show low intensities and then high intensities
        # This is because we are interested in high intensity regions
        sorted_ind = np.argsort(overlay)
        embedding = embedding[sorted_ind]
        overlay = overlay[sorted_ind]

    # Create the plot
    fig = plt.figure(figsize=(15, 12))

    plt.axis('off')
    fig.patch.set_facecolor(('black'))

    plt.scatter(embedding[:, 0], embedding[:, 1], c=overlay, alpha=0.5, s=15)

    plt.savefig(Path(backend_config['temp-folder'], dr_folder, 'embedding.png'), bbox_inches='tight', transparent=True)

    return True


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


def get_embedding(args: dict[str, str]) -> bool:
    """Compute the embedding based on the given arguments.

    :param args: A dictionary containing the arguments for generating the embedding.
    :return: True if the embedding was successfully generated. Otherwise False.
    """

    # Compute the embedding
    if not generate_embedding({key: args[key] for key in DR_ARGS if key in args.keys()}):
        LOG.error("Failed to compute DR embedding")
        return False
    
    LOG.info("Generated embedding successfully")
    return True