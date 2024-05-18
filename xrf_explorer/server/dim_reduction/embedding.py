import logging 

from pathlib import Path

import numpy as np

from xrf_explorer.server.file_system.config_handler import load_yml

LOG: logging.Logger = logging.getLogger(__name__)

DR_ARGS: list[str] = ['element', 'threshold', 'n-neighbors', 'min-dist', 'n-components', 'metric']


def apply_umap(data: np.ndarray, n_neighbors: int, min_dist: float, n_components: int, metric: str) -> np.ndarray | None:
    """Reduces the dimensionality of the given data using uniform manifold approximation and projection (UMAP).
    The original data is not modified. For more information on UMAP, see: https://umap-learn.readthedocs.io/en/latest/.

    :param data: array, shape (n_samples, n_features). The data on which UMAP is used to reduce the dimension of n-features to n_components. 
    :param n_neighbors: The size of local neighborhood. See UMAP documentation for more information.
    :param min_dist: The minimum distance between points in the embedding. See UMAP documentation for more information.
    :param n_components: The dimension of the embedded space. See UMAP documentation for more information.
    :param metric: The metric to use for distance computation. See UMAP documentation for more information.
    :return: array, shape (n_samples, n_components) containing the result of UMAP applied to given data with the given parameters. 
    If UMAP fails, None is returned.
    """

    from umap import UMAP

    try:
        embedding = UMAP(
            n_neighbors=n_neighbors,
            min_dist=min_dist,
            n_components=n_components, 
            metric=metric
        ).fit_transform(data)
    
        return embedding
    except:
        return None

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
    LOG.info(f"Generating embedding with:\n"
             f"\telement: {element},\n"
             f"\tthreshold: {threshold},\n"
             f"\tsize: {filtered_data.shape}")
    
    embedded_data: np.ndarray | None = apply_umap(
        filtered_data,
        int(dr_config['n-neighbors']), 
        float(dr_config['min-dist']), 
        int(dr_config['n-components']), 
        dr_config['metric']
    )

    if embedded_data is None:
        LOG.error(f"Failed to compute embedding")
        return False

    # save indices and embedded data
    np.save(Path(backend_config['temp-folder'], dr_config['folder'], 'indices.npy'), indices)
    np.save(Path(backend_config['temp-folder'], dr_config['folder'], 'embedded_data.npy'), embedded_data)

    LOG.info("Generated embedding successfully")
    return True
