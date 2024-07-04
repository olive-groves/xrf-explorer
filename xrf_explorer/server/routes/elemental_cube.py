import json

from io import BytesIO
from logging import Logger, getLogger

import numpy as np

from PIL.Image import Image, fromarray
from flask import request, send_file

from xrf_explorer import app

from xrf_explorer.server.file_system.cubes import (
    convert_elemental_cube_to_dms,
    get_element_averages,
    get_element_averages_selection,
    get_element_names,
    get_elemental_datacube_dimensions,
    get_elemental_map,
    normalize_ndarray_to_grayscale
)

from xrf_explorer.server.file_system.workspace import (
    get_workspace_dict,
    get_elemental_cube_recipe_path,
    get_elemental_cube_path
)

from xrf_explorer.server.image_register import load_points_dict
from xrf_explorer.server.image_to_cube_selection import CubeType
from xrf_explorer.server.routes.helper import encode_selection

LOG: Logger = getLogger(__name__)


@app.route("/api/<data_source>/data/size")
def data_cube_size(data_source: str):
    """
    Get the size of the data cubes.


    :param data_source: data source to get the size from
    :return: the size of the data cubes
    """

    # this does not work for elemental datacubes in the csv format
    width, height, _, _ = get_elemental_datacube_dimensions(data_source)

    # Return the width and height
    return {
        "width": width,
        "height": height
    }, 200


@app.route("/api/<data_source>/data/recipe")
def data_cube_recipe(data_source: str):
    """
    Get the registering recipe for the data cubes.

    :param data_source: data source to get the recipe from
    :return: the registering recipe of the data cubes
    """

    # As the XRF Explorer only supports a single data cube, we take the recipe of the first elemental cube
    path: str | None = get_elemental_cube_recipe_path(data_source)
    if not path:
        return f"Could not find recipe for data cubes in source {data_source}", 404

    # Get the recipe points
    points: dict = load_points_dict(path)
    if not points:
        return f"Could not find registering points at {path}", 404

    return points, 200


@app.route("/api/<data_source>/data/elements/names")
def list_element_names(data_source: str):
    """
    Get the short names of the elements stored in the elemental data cube.

    :param data_source: data source to get the element names from
    :return: JSON list of the short names of the elements.
    """
    return json.dumps(get_element_names(data_source))


@app.route("/api/<data_source>/data/elements/map/<int:channel>")
def elemental_map(data_source: str, channel: int):
    """
    Get an elemental map.

    :param data_source: data source to get the map from
    :param channel: the channel to get the map from
    :return: the elemental map
    """

    # As the XRF Explorer only supports a single data cube, we do not have to do any wizardry to stitch maps together
    path: str | None = get_elemental_cube_path(data_source)
    if path is None:
        return f"Could not find elemental data cube in source {data_source}", 404

    # Get the elemental map
    image_array: np.ndarray = get_elemental_map(channel, path)
    image_normalized: np.ndarray = normalize_ndarray_to_grayscale(image_array)
    image: Image = fromarray(image_normalized).convert("L")

    # Save the image to an io buffer
    image_io = BytesIO()
    image.save(image_io, "png")
    image_io.seek(0)

    # Serve the image and ensure that the converted images are cached by the client
    response = send_file(image_io, mimetype='image/png')
    response.headers["Cache-Control"] = "public, max-age=604800, immutable"
    return response


@app.route("/api/<data_source>/data/convert")
def convert_elemental_cube(data_source: str):
    """
    Converts all elemental data cubes of a data source to .dms format.

    :param data_source: The name of the data source to convert the elemental data cube
    :return: 200 if the conversion was successful, 500 otherwise
    """

    # Get elemental data cube paths
    workspace_dict = get_workspace_dict(data_source)
    if workspace_dict is None:
        return "Error getting elemental datacube path", 500

    cube_names: list[str] = [cube_info["name"] for cube_info in workspace_dict["elementalCubes"]]

    # Convert each elemental data cube
    for cube_name in cube_names:
        success: bool = convert_elemental_cube_to_dms(data_source, cube_name)
        if not success:
            return "Error converting elemental data cube to .dms format", 500

    return "Converted elemental data cube to .dms format", 200


@app.route("/api/<data_source>/element_averages", methods=["POST", "GET"])
def list_element_averages(data_source: str):
    """
    Get the names and averages of the elements present in the painting.

    :param data_source: data_source to get the element averages from
    :return: JSON list of objects indicating average abundance for every element. Each object is of the form
        {
            name: element name,
            average: element abundance
        }
    """
    return json.dumps(get_element_averages(data_source))


@app.route("/api/<data_source>/element_averages_selection", methods=["POST"])
def list_element_averages_selection(data_source: str):
    """
    Get the names and averages of the elements present in a rectangular selection of the painting.

    :param data_source: data_source to get the element averages from
    :return: JSON list of objects indicating average abundance for every element. Each object is of the form
        {
            name: element name,
            average: element abundance
        }
    """
    mask: np.ndarray | tuple[str, int] = encode_selection(request.get_json(), data_source, CubeType.Elemental)

    if isinstance(mask, tuple):
        return mask[0], mask[1]

    # get averages
    composition: list[dict[str, str | float]] = get_element_averages_selection(data_source, mask)

    try:
        return json.dumps(composition)
    except Exception as e:
        LOG.error(f"Failed to serialize element averages: {str(e)}")
        return "Error occurred while listing element averages", 500
