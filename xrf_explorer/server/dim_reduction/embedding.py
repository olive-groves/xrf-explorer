import logging

from os import mkdir
from os.path import isdir, join

import numpy as np
from umap import UMAP

from xrf_explorer.server.file_system.config_handler import get_config
from xrf_explorer.server.file_system import (
    get_elemental_data_cube, get_elemental_cube_path, normalize_ndarray_to_grayscale
)
from xrf_explorer.server.dim_reduction.general import valid_element, get_path_to_dr_folder

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
        embedding: np.ndarray = UMAP(
            n_neighbors=n_neighbors,
            min_dist=min_dist,
            n_components=n_components,
            metric=metric
        ).fit_transform(data)

        return embedding
    except:
        return None


def filter_elemental_cube(elemental_cube: np.ndarray, element: int, 
                          threshold: int, max_indices: int) -> tuple[np.ndarray, bool]:
    """Get indices for which the value of the given element in the normalized elemental data cube is above the threshold.

    :param elemental_cube: shape (3, m, n) elemental data cube.
    :param element: The element to filter on.
    :param threshold: The threshold to filter by.
    :param max_indices: The maximum number of indices to return.
    :return: Indices for which the value of the given element in the normalized elemental data cube is above the threshold; boolean whether the indices were downsampled.
    """

    # normalize the elemental map to [0, 255]
    # this is done so the threshold can be applied
    normalized_elemental_map: np.ndarray = normalize_ndarray_to_grayscale(elemental_cube[element])
    
    # get all indices for which the intensity of the given element is above the threshold
    indices: np.ndarray = np.argwhere(normalized_elemental_map >= threshold)

    # check if the number of indices is higher than the configured limit
    # if so, the indices are randomly downsampled
    down_sampled: bool = False
    if indices.shape[0] > max_indices:
        LOG.info("Number of data points for dimensionality reduction is higher than the configured limit. "
                 "Points will be randomly downsampled, (%i -> %i)", indices.shape[0], max_indices)
        
        # Use default rng to ensure random selection every time
        indices = indices[np.random.default_rng().choice(indices.shape[0], size=max_indices)]
        down_sampled = True

    # return the filtered indices
    return indices, down_sampled


def generate_embedding(data_source: str, element: int, threshold: int, new_umap_parameters: dict[str, str] = {}) -> str:
    """Generate the embedding (lower dimensional representation of the data) of the
    elemental data cube using the dimensionality reduction method "UMAP". The embedding 
    with the list of indices (which pixels from the elemental data cube are in the embedding) 
    are stored in the folder specified in the backend config file. The order the indices
    occur in the indices list is the same order as the positions of the mapped pixels in 
    the embedding.

    :param data_source: The name of the data source to generate the embedding for.
    :param element: The element to generate the embedding for.
    :param threshold: The threshold to filter the data cube by.
    :param new_umap_parameters: The parameters passed on to the UMAP algorithm.
    :return: string code indicating the status of the embedding generation. "error" when error occurred, "success" when embedding was generated successfully, "downsampled" when successful and the number of data points was downsampled.
    """

    # load backend config
    backend_config: dict = get_config()
    if not backend_config:  # config is empty
        LOG.error("Failed to compute DR embedding")
        return "error"

    # get default dim reduction config
    umap_parameters: dict[str, str] = backend_config['dim-reduction']['umap-parameters']

    # update the default parameters with the given parameters
    umap_parameters.update(new_umap_parameters)

    # get data cube
    path_to_cube: str = get_elemental_cube_path(data_source)
    data_cube: np.ndarray = get_elemental_data_cube(path_to_cube)
    if len(data_cube) == 0:
        return "error"

    # check if element is valid
    if not valid_element(element, data_cube):
        return "error"

    # filter data
    max_samples: int = int(backend_config['dim-reduction']['max-samples'])
    indices, down_sampled = filter_elemental_cube(data_cube, element, threshold, max_samples)
    filtered_data: np.ndarray = data_cube[:, indices[:, 0], indices[:, 1]].transpose()

    # compute embedding
    LOG.info(f"Generating embedding with:\n"
             f"\telement: {element},\n"
             f"\tthreshold: {threshold},\n"
             f"\tsize: {filtered_data.shape}")

    embedded_data: np.ndarray | None = apply_umap(
        filtered_data,
        int(umap_parameters['n-neighbors']),
        float(umap_parameters['min-dist']),
        int(umap_parameters['n-components']),
        umap_parameters['metric']
    )

    if embedded_data is None:
        LOG.error("Failed to compute embedding")
        return "error"

    # get path to folder to store the embedding and the indices
    dr_folder: str = get_path_to_dr_folder(data_source)

    # Check if the folder exists, otherwise create it
    if not isdir(dr_folder):
        LOG.error(f"Creating folder: {dr_folder}")
        mkdir(dr_folder)

    # save indices and embedded data
    np.save(join(dr_folder, 'indices.npy'), indices)
    np.save(join(dr_folder, 'embedded_data.npy'), embedded_data)

    LOG.info("Generated embedding successfully")
    if down_sampled:
        return "downsampled"
    return "success"
