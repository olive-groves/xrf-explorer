import logging 

from os.path import join
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from xrf_explorer.server.file_system.config_handler import load_yml

LOG: logging.Logger = logging.getLogger(__name__)

# Constants
ELEMENT = 9
THRESHOLD = 100

def apply_umap(data):
    from umap import UMAP 

    return UMAP(
        n_neighbors=10,
        min_dist=0,
        n_components=2, 
        metric= 'cosine'
    ).fit_transform(data)

def perform_dim_reduction(config_path: str = "config/backend.yml") -> bool:
    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        return None
    
    # get data cube path
    data_cube_path: Path = Path(backend_config['uploads-folder'], 'test_cube.npy')
    if not data_cube_path:
        return False

    # load data cube
    data = np.load(data_cube_path)

    # filter data
    indices = np.argwhere(data[:, :, ELEMENT] >= THRESHOLD)

    # get filtered data
    spectra = data[indices[:, 0], indices[:, 1], :]

    # compute embedding
    embedded_data = apply_umap(spectra)

    # save indices and embedded data
    np.save(Path(backend_config['temp-folder'], 'indices.npy'), indices)
    np.save(Path(backend_config['temp-folder'], 'embedded_data.npy'), embedded_data)

    return True

def create_embedding_image(config_path: str = "config/backend.yml"):
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
    plt.figure(figsize=(15, 12))

    plt.scatter(embedding[:, 0], embedding[:, 1], c=overlay, alpha=0.5/2, s=15)
    plt.colorbar()

    plt.savefig(Path(backend_config['temp-folder'], 'embedding.png'))

    return True