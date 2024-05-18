import logging 

from pathlib import Path

import numpy as np

from xrf_explorer.server.file_system.config_handler import load_yml

LOG: logging.Logger = logging.getLogger(__name__)

DR_ARGS: list[str] = ['element', 'threshold', 'n-neighbors', 'min-dist', 'n-components', 'metric']


def apply_umap(data, parms: dict[str, str]):
    """Apply UMAP to the given data with the given parameters.

    :param data: Data to apply UMAP to.
    :param parms: A dictionary containing the parameters for UMAP.
    :return: The embedded data.
    """

    from umap import UMAP

    return UMAP(
        n_neighbors=int(parms['n-neighbors']),
        min_dist=float(parms['min-dist']),
        n_components=int(parms['n-components']), 
        metric= parms['metric']
    ).fit_transform(data)


def filter_elemental_cube(data_cube, element: int, threshold: int):
    """Filter the given data based on the given element and threshold.
    
    :param data: 3D-Numpy array.
    :param element: The element to filter on.
    :param threshold: The threshold to filter by.
    :return: Indices for which the value of the given element in the data is above the threshold.
    """
    # get all indices for which the intensity of the given element is above the threshold
    indices = np.argwhere(data_cube[:, :, element] >= threshold)

    # return the filtered indices
    return indices


def generate_embedding(args: dict[str, str], config_path: str = "config/backend.yml") -> bool:
    """Generate the embedding of the elemental data cube.

    :param args: Arguments for generating the embedding. Should at least contain the element.
    :param config_path: Path to the backend config file
    :return: True if the embedding was successfully generated. Otherwise False.
    """
    # Compute the embedding
    args = {key: args[key] for key in DR_ARGS if key in args.keys()}

    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        LOG.error("Failed to compute DR embedding")
        return False
    
    # get default dim reduction config
    dr_config: dict = backend_config['dim-reduction']
    dr_config.update(args)

    # Constants
    element = int(dr_config['element'])
    threshold = int(dr_config['threshold'])

    # get data cube
    data_cube_path: Path = Path(backend_config['uploads-folder'], 'test_cube.npy') # TODO change this to the actual data cube
    data_cube = np.load(data_cube_path)
    LOG.info(f"Loaded data cube from: {data_cube_path}")

    # check if element is valid
    if element < 0 or element >= data_cube.shape[2]:
        LOG.error(f"Invalid element: {element}")
        return False

    # filter data
    indices = filter_elemental_cube(data_cube, element, threshold)
    filtered_data = data_cube[indices[:, 0], indices[:, 1], :]

    # compute embedding
    LOG.info(f"Generating embedding with: el {element}, tr {threshold}, size {filtered_data.shape}")
    try:
        embedded_data = apply_umap(filtered_data, dr_config)
    except:
        LOG.error(f"Failed to compute embedding with: {dr_config}")
        return False

    # save indices and embedded data
    np.save(Path(backend_config['temp-folder'], dr_config['folder'], 'indices.npy'), indices)
    np.save(Path(backend_config['temp-folder'], dr_config['folder'], 'embedded_data.npy'), embedded_data)

    LOG.info("Generated embedding successfully")
    return True
