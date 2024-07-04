import json

from logging import Logger, getLogger
from os.path import join, exists, abspath

import numpy as np

from flask import jsonify, send_file

from xrf_explorer import app

from xrf_explorer.server.color_segmentation import (
    get_path_to_cs_folder,
    get_clusters_using_k_means,
    get_elemental_clusters_using_k_means,
    combine_bitmasks,
    convert_to_hex,
    save_bitmask_as_png
)

from xrf_explorer.server.file_system import get_config
from xrf_explorer.server.file_system.workspace import get_base_image_name
from xrf_explorer.server.routes.helper import validate_config

LOG: Logger = getLogger(__name__)


@app.route('/api/<data_source>/cs/clusters/<int:elem>/<int:k>/<int:elem_threshold>', methods=['GET'])
def get_color_clusters(data_source: str, elem: int, k: int, elem_threshold: int):
    """
    Gets the colors corresponding to the image-wide/element-wise color clusters, and caches them as well as the
    corresponding bitmasks.

    :param data_source: data source to get the clusters from
    :param elem: index of selected element (0 if whole painting, channel+1 if element)
    :param k: number of color clusters to compute
    :param elem_threshold: elemental threshold
    :return JSON containing the ordered list of colors
    """
    # Get rgb image name and path
    rgb_image_name: str | None = get_base_image_name(data_source)
    if rgb_image_name is None:
        return 'Error occurred while getting rgb image name', 500

    config: dict | None = get_config()
    if config is None:
        return 'Error occurred while getting backend config', 500

    # Path to cache data
    path_to_save: str = get_path_to_cs_folder(data_source)

    # path to json for caching color
    full_path_json: str
    if elem == 0:
        full_path_json = join(path_to_save, f'colors_painting_{k}.json')
    else:
        full_path_json = join(path_to_save, f'colors_{elem - 1}_{k}_{elem_threshold}.json')

    # If json already exists, return that directly
    if exists(full_path_json):
        with open(full_path_json, 'r') as json_file:
            color_data: np.ndarray = json.load(json_file)
        return jsonify(color_data)

    # Path to save bitmasks
    bitmask_full_path: str

    # elem == 0 indicates clusters for the whole painting
    if elem == 0:
        LOG.info('Computing color clusters for whole image')
        # Compute colors and bitmasks
        colors: np.ndarray
        bitmasks: np.ndarray
        colors, bitmasks = get_clusters_using_k_means(data_source, rgb_image_name, k)
        bitmask_full_path: str = join(path_to_save, f'bitmask_painting_{k}.png')
    else:
        LOG.info(f'Computing color clusters for single element: {elem - 1}')
        scaled_elem_threshold: int = int(255 * elem_threshold / 100)
        # Compute colors and bitmasks per element
        colors: np.ndarray
        bitmasks: np.ndarray
        colors, bitmasks = get_elemental_clusters_using_k_means(
            data_source, rgb_image_name, elem - 1, scaled_elem_threshold, k
        )
        bitmask_full_path: str = join(path_to_save, f'bitmask_{elem - 1}_{k}_{elem_threshold}.png')

    # Combine bitmasks into one
    combined_bitmask: np.ndarray = combine_bitmasks(bitmasks)
    colors = convert_to_hex(colors)

    # Cache bitmask data
    image_saved: bool = save_bitmask_as_png(combined_bitmask, bitmask_full_path)
    if not image_saved:
        return f'Error occurred while saving bitmask for element {elem} as png', 500

    # Cache color data
    with open(full_path_json, 'w') as json_file:
        json.dump(colors, json_file)

    return json.dumps(colors)


@app.route('/api/<data_source>/cs/bitmask/<int:elem>/<int:k>/<int:elem_threshold>', methods=['GET'])
def get_color_cluster_bitmask(data_source: str, elem: int, k: int, elem_threshold: int):
    """
    Returns the png bitmask for the color clusters over the whole painting/selected element.

    :param data_source: data_source to get the bitmask from
    :param elem: index of selected element (0 if whole painting, channel+1 if element)
    :param k: number of color clusters to compute
    :param elem_threshold: elemental threshold
    :return bitmask PNG file for the whole image
    """
    LOG.info(f'Bitmasks for k={k}, elem={elem}, elem_threshold={elem_threshold}')
    config: dict | None = get_config()

    error_response_config: tuple[str, int] | None = validate_config(config)
    if error_response_config:
        return error_response_config

    # Path to save bitmask to
    path_to_save: str = get_path_to_cs_folder(data_source)
    if not path_to_save:
        return 'Error occurred while getting path to save bitmask to', 500

    bitmask_full_path: str
    if elem == 0:
        bitmask_full_path: str = join(path_to_save, f'bitmask_painting_{k}.png')
    else:
        bitmask_full_path: str = join(path_to_save, f'bitmask_{elem - 1}_{k}_{elem_threshold}.png')

    # If image doesn't exist, compute clusters
    if not exists(bitmask_full_path):
        get_color_clusters(data_source, elem, k, elem_threshold)

    return send_file(abspath(bitmask_full_path), mimetype='image/png')
