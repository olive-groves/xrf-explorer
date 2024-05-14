import logging 

from pathlib import Path

from flask import send_file

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from xrf_explorer.server.file_system.config_handler import load_yml

LOG: logging.Logger = logging.getLogger(__name__)

DR_ARGS = ['element', 'threshold', 'n_neighbors', 'min_dist', 'n_components', 'metric']
OVERLAY_ARGS = ['type']


def apply_umap(data, parms):
    from umap import UMAP

    return UMAP(
        n_neighbors=int(parms['n_neighbors']),
        min_dist=float(parms['min_dist']),
        n_components=int(parms['n_components']), 
        metric= parms['metric']
    ).fit_transform(data)


def generate_embedding(args: dict[str, str], config_path: str = "config/backend.yml") -> bool:
    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        return False
    
    # get default dim reduction config
    dr_config: dict = backend_config['default_dim_reduction']
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
    LOG.info(f"Generating embedding with: el {element}, tr {threshold}")
    try:
        embedded_data = apply_umap(spectra, dr_config)
    except ValueError as e:
        LOG.error(f"Failed to compute embedding: {e}")
        return False

    # save indices and embedded data
    np.save(Path(backend_config['temp-folder'], 'indices.npy'), indices)
    np.save(Path(backend_config['temp-folder'], 'embedded_data.npy'), embedded_data)

    return True


def create_embedding_image(args: dict[str, str], config_path: str = "config/backend.yml"):
    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        return None
    
    # Constants 
    ELEMENT_OVERLAY = 9

    # Load the file embedding.npy
    indices = np.load(Path(backend_config['temp-folder'], 'indices.npy'))
    embedding = np.load(Path(backend_config['temp-folder'], 'embedded_data.npy'))

    overlay = np.load(Path(backend_config['uploads-folder'], 'test_cube.npy'))[indices[:, 0], indices[:, 1], ELEMENT_OVERLAY]

    # We want to first show low intensities and then high intensities
    # This is because we are interested in high intensity regions
    sorted_ind = np.argsort(overlay)
    overlay = overlay[sorted_ind]
    embedding = embedding[sorted_ind]

    # Create the plot
    fig = plt.figure(figsize=(15, 12))

    plt.axis('off')
    fig.patch.set_facecolor(('black'))

    plt.scatter(embedding[:, 0], embedding[:, 1], c=overlay, alpha=0.5/2, s=15)
    # plt.colorbar()

    plt.savefig(Path(backend_config['temp-folder'], 'embedding.png'), bbox_inches='tight')

    return True


def get_embedding_image(args):
    # Create the embedding image
    if not create_embedding_image({key: args[key] for key in OVERLAY_ARGS if key in args.keys()}):
        LOG.error("Failed to create DR embedding image")
        return "Failed to create DR embedding image", 400
    
    # Return the embedding
    LOG.info("Created embedding image successfully")
    embedding_path = "server/temp/embedding.png" # TODO: Fix this path
    return send_file(embedding_path, mimetype='image/png')


def get_embedding(args):
    # Compute the embedding
    if not generate_embedding({key: args[key] for key in DR_ARGS if key in args.keys()}):
        LOG.error("Failed to compute DR embedding")
        return "Failed to compute DR embedding", 400
    
    LOG.info("Generated embedding successfully")
    return "Generated embedding successfully"