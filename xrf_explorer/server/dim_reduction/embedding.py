import logging

from os.path import join, abspath

import numpy as np
import umap

from xrf_explorer.server.file_system.config_handler import load_yml
from xrf_explorer.server.dim_reduction.general import valid_element, get_elemental_data_cube

LOG: logging.Logger = logging.getLogger(__name__)


def apply_umap(data: np.ndarray, n_neighbors: int, min_dist: float, n_components: int,
               metric: str) -> np.ndarray | None:
    """Reduces the dimensionality of the given data using uniform manifold approximation and projection (UMAP).
    The original data is not modified. For more information on UMAP, see: https://umap-learn.readthedocs.io/en/latest/.

    :param data: np.ndarray, shape (n_samples, n_features). The data on which UMAP is used to reduce the dimension of -features to n_components.
    :param n_neighbors: The size of local neighborhood. See UMAP documentation for more information.
    :param min_dist: The minimum distance between points in the embedding. See UMAP documentation for more information.
    :param n_components: The dimension of the embedded space. See UMAP documentation for more information.
    :param metric: The metric to use for distance computation. See UMAP documentation for more information.
    :return: np.ndarray, shape (n_samples, n_components) containing the result of UMAP applied to given data with the given parameters. If UMAP fails, None is returned.
    """

    try:
        embedding: np.ndarray = umap.UMAP(
            n_neighbors=n_neighbors,
            min_dist=min_dist,
            n_components=n_components,
            metric=metric
        ).fit_transform(data)

        return embedding
    except:
        return None


def filter_elemental_cube(elemental_cube: np.ndarray, element: int, threshold: int) -> np.ndarray:
    """Get indices for which the value of the given element in the elemental data cube is above the threshold.

    :param elemental_cube: shape (n, m, 3) elemental data cube.
    :param element: The element to filter on.
    :param threshold: The threshold to filter by.
    :return: Indices for which the value of the given element in the elemental data cube is above the threshold.
    """
    # get all indices for which the intensity of the given element is above the threshold
    indices: np.ndarray = np.argwhere(elemental_cube[:, :, element] >= threshold)

    # return the filtered indices
    return indices


def generate_embedding(element: int, threshold: int, umap_parameters: dict[str, str] = {},
                       config_path: str = "config/backend.yml") -> bool:
    """Generate the embedding (lower dimensional representation of the data) of the
    elemental data cube using the dimensionality reduction method "UMAP". The embedding 
    with the list of indices (which pixels from the elemental data cube are in the embedding) 
    are stored in the folder specified in the backend config file. The order the indices
    occur in the indices list is the same order as the positions of the mapped pixels in 
    the embedding.

    :param element: The element to generate the embedding for.
    :param threshold: The threshold to filter the data cube by.
    :param umap_parameters: The parameters passed on to the UMAP algorithm.
    :param config_path: Path to the backend config file.
    :return: True if the embedding was successfully generated. Otherwise, False.
    """

    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        LOG.error("Failed to compute DR embedding")
        return False

    # get default dim reduction config
    default_umap_parameters: dict[str, str] = backend_config['dim-reduction']['umap-parameters']

    # update default umap parameters with the given umap parameters
    modified_umap_parameters: dict[str, str] = umap_parameters.copy()
    modified_umap_parameters.update(default_umap_parameters)

    # get data cube
    data_cube: np.ndarray | None = get_elemental_data_cube(config_path=config_path)

    if data_cube is None:
        return False

    # check if element is valid
    if not valid_element(element, data_cube):
        return False

    # filter data
    indices: np.ndarray = filter_elemental_cube(data_cube, element, threshold)
    filtered_data: np.ndarray = data_cube[indices[:, 0], indices[:, 1], :]

    # compute embedding
    LOG.info(f"Generating embedding with:\n"
             f"\telement: {element},\n"
             f"\tthreshold: {threshold},\n"
             f"\tsize: {filtered_data.shape}")

    embedded_data: np.ndarray | None = apply_umap(
        filtered_data,
        int(modified_umap_parameters['n-neighbors']),
        float(modified_umap_parameters['min-dist']),
        int(modified_umap_parameters['n-components']),
        modified_umap_parameters['metric']
    )

    if embedded_data is None:
        LOG.error("Failed to compute embedding")
        return False

    # save indices and embedded data
    folder_to_store: str = backend_config['dim-reduction']['folder']
    np.save(join(abspath(folder_to_store), 'indices.npy'), indices)
    np.save(join(abspath(folder_to_store), 'embedded_data.npy'), embedded_data)

    LOG.info("Generated embedding successfully")
    return True
