import json

from logging import Logger, getLogger
from os.path import join, exists, abspath

import numpy as np

from flask import send_file, request

from xrf_explorer import app

from xrf_explorer.server.color_segmentation import (
    get_path_to_cs_folder,
    get_clusters_using_k_means,
    get_elemental_clusters_using_k_means,
    combine_bitmasks,
    convert_to_hex,
    save_bitmask_as_png
)
from xrf_explorer.server.image_to_cube_selection import CubeType
from xrf_explorer.server.file_system import get_config
from xrf_explorer.server.file_system.workspace import get_base_image_name
from xrf_explorer.server.routes.helper import validate_config, encode_selection

LOG: Logger = getLogger(__name__)


@app.route('/api/<data_source>/cs/clusters/<int:k>/<uses_selection>', methods=['POST'])
def get_color_clusters(data_source: str, k: int, uses_selection: str = "false"):
    """
    Gets the colors corresponding to the image-wide/element-wise color clusters, and caches them as well as the
    corresponding bitmasks.

    :param data_source: data source to get the clusters from
    :param k: number of color clusters to compute
    :param uses_selection: whether the clustering will be calculated over the provided selection or not
    :param JSON payload: contains a dictionary with:
        "elements": pairs of element and threshold
        "selection": SelectionAreaSelection object for the selection
    :return JSON containing the ordered list of colors
    """
    # Get rgb image name and path
    rgb_image_name: str | None = get_base_image_name(data_source)
    if rgb_image_name is None:
        return 'Error occurred while getting rgb image name', 500

    config: dict | None = get_config()
    if config is None:
        return 'Error occurred while getting backend config', 500

    #read payload
    payload = request.get_json()
    selection = payload["selection"]
    elements = payload["elements"]

    uses_selection = True if uses_selection == "true" else False

    # Path to save bitmask to
    path_to_save: str = get_path_to_cs_folder(data_source)
    if not path_to_save:
        return 'Error occurred while getting path to save bitmask to', 500

    bitmask_full_path: str = join(path_to_save, f'bitmask.png')

    # path to json for color clusters
    full_path_json: str = join(path_to_save, f'colors_selection.json')

    # If json already exists, return that directly
    #if exists(full_path_json) and not uses_selection:
    #    with open(full_path_json, 'r') as json_file:
    #        color_data: np.ndarray = json.load(json_file)
    #    return json.dumps(color_data)

    # Path to save bitmasks
    bitmask_full_path: str
    colors: np.ndarray
    bitmasks: list[np.ndarray]
    selection_mask: np.ndarray | tuple[str, int]
    selection_mask = encode_selection(selection, data_source, CubeType.Elemental)

    # elem == 0 indicates clusters for the whole painting
    # if len(elements) == 1, the whole painting is the only channel to be clustered
    # if len(elements) != 1, the whole painting channel can be ignored, since the
    # intersection of the whole painting and an element is the element
    if len(elements) == 1 and elements[0][0] == 0:
        LOG.info('Computing color clusters for whole image')
        # Compute colors and bitmasks
        colors: np.ndarray
        bitmasks: list[np.ndarray]

        if isinstance(selection_mask, tuple):
            return selection_mask[0], selection_mask[1]

        colors, bitmasks = get_clusters_using_k_means(data_source, rgb_image_name, selection_mask, k)
        #bitmask_full_path: str = join(path_to_save, f'bitmask_painting_{k}_{uses_selection}.png')
    else:
        LOG.info(f'Computing color clusters for elements: {elements}')

        # Compute colors and bitmasks per element
        if isinstance(selection_mask, tuple):
            return selection_mask[0], selection_mask[1]

        # Create the correct lists to send to the color segmentation function
        elementList = []
        thresholdList = []
        for i in range (len(elements)):
            if elements[i][0] != 0: #ignore whole painting channel
                elementList.append(elements[i][0] - 1)
                thresholdList.append(int(255 * elements[i][1] / 100))

        colors, bitmasks = get_elemental_clusters_using_k_means(
            data_source, rgb_image_name, np.array(elementList), selection_mask, np.array(thresholdList), k
        )
        #bitmask_full_path: str = join(path_to_save, f'bitmask_{elements[0][0] - 1}_{k}_{elements[0][1]}_{uses_selection}.png')

        LOG.info("Color segmentation bitmask: " + full_path_json)

    # Combine bitmasks into one
    combined_bitmask: np.ndarray = combine_bitmasks(bitmasks)
    colors = convert_to_hex(colors)

    # Cache bitmask data
    image_saved: bool = save_bitmask_as_png(combined_bitmask, bitmask_full_path)
    if not image_saved:
        return f'Error occurred while saving bitmask for color segmentation as png', 500

    # Cache color data
    with open(full_path_json, 'w') as json_file:
        json.dump(colors, json_file)

    return json.dumps(colors)


@app.route('/api/<data_source>/cs/bitmask', methods=['GET'])
def get_color_cluster_bitmask(data_source: str):
    """
    Returns the last generated bitmask for color segmentation

    :param data_source: data_source to get the bitmask from
    :return most recently generated bitmask
    """
    LOG.info(f'Grabbing most recent bitmask')
    config: dict | None = get_config()

    error_response_config: tuple[str, int] | None = validate_config(config)
    if error_response_config:
        return error_response_config

    # Path to save bitmask to
    path_to_save: str = get_path_to_cs_folder(data_source)
    if not path_to_save:
        return 'Error occurred while getting path to save bitmask to', 500

    bitmask_full_path: str = join(path_to_save, f'bitmask.png')

    # If image doesn't exist, compute clusters
    if not exists(bitmask_full_path):
        LOG.info(f'Could not find bitmask for color segmentation')

    return send_file(abspath(bitmask_full_path), mimetype='image/png')
