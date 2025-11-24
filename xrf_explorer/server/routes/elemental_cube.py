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
from xrf_explorer.server.file_system.cubes.convert_csv import get_elemental_data_cube_from_csv
from xrf_explorer.server.file_system.cubes.convert_dms import get_elemental_data_cube_from_dms
from xrf_explorer.server.file_system.cubes.spectral import parse_rpl

from xrf_explorer.server.file_system.workspace import (
    get_workspace_dict,
    get_elemental_cube_recipe_path,
    get_elemental_cube_path
)
from xrf_explorer.server.file_system.workspace.file_access import (
    get_elemental_cube_path_from_name,
    get_elemental_cube_file_names,
    get_base_image_path,
    get_path_to_workspace
)
from xrf_explorer.server.file_system.helper import get_path_to_generated_folder, get_config
from PIL.Image import fromarray
import os
import uuid
import json

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
            channel: element channel,
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

@app.route("/api/<data_source>/grayscale/from_elemental_cube", methods=["POST"])
def create_grayscale_from_elemental_cube(data_source: str):
    """
    Create a grayscale PNG from an elemental cube layer and persist it in the uploads folder.

    Body JSON: { "cubeName": "name", "layer": <int> (optional), "outputName": "optional-filename.png" (optional) }
    Returns the grayscale metadata object to be included in workspace.grayscale
    """
    try:
        body = request.get_json()
        cube_name: str = body.get("cubeName")
        layer: int | None = body.get("layer")
        output_name: str | None = body.get("outputName")
    except Exception:
        LOG.error("Invalid JSON body for grayscale creation request")
        return "Invalid request body", 400

    LOG.info(f"grayscale request for data_source={data_source}, cubeName={cube_name}, layer={layer}")

    if not cube_name:
        LOG.error("Missing cubeName in grayscale request")
        return "Missing cubeName", 400

    # Resolve cube path
    cube_path = get_elemental_cube_path_from_name(data_source, cube_name)
    cube = None
    is_elemental = False
    # Try to find elemental cube by name
    load_path: str | None = None
    try:
        if cube_path is not None:
            load_path = cube_path
            is_elemental = True
        else:
            # check partialElementalCubes in workspace
            workspace = get_workspace_dict(data_source)
            if workspace is None:
                return "Workspace not found", 404
            for cube_info in workspace.get("partialElementalCubes", []) or []:
                if cube_info.get("name") == cube_name:
                    backend_config = get_config()
                    uploads_folder = backend_config["uploads-folder"]
                    load_path = os.path.join(uploads_folder, data_source, cube_info.get("dataLocation"))
                    is_elemental = True
                    break
    except Exception as e:
        LOG.error(f"Error while resolving elemental cube path: {e}")
        return "Failed to resolve elemental cube path", 500

    if load_path is not None:
        # Load elemental cube from path
        try:
            if load_path.endswith('.csv'):
                cube = get_elemental_data_cube_from_csv(load_path)
            elif load_path.endswith('.dms'):
                cube = get_elemental_data_cube_from_dms(load_path)
            else:
                LOG.error(f"Unknown elemental cube format for {load_path}")
                return "Unknown elemental cube format", 500

            if cube is None or cube.size == 0:
                return "Failed to read elemental cube", 500
        except Exception as e:
            LOG.error(f"Error reading elemental cube from path {load_path}: {e}")
            return "Failed to read elemental cube", 500
    else:
        # Try spectral cube with given name
        workspace = get_workspace_dict(data_source)
        if workspace is None:
            return "Workspace not found", 404

        spectral_lists = []
        spectral_lists.extend(workspace.get("partialSpectralCubes", []) or [])
        spectral_lists.extend(workspace.get("spectralCubes", []) or [])

        matched = None
        for s in spectral_lists:
            if s.get("name") == cube_name:
                matched = s
                break

        if matched is None:
            return f"Cube {cube_name} not found (not elemental nor spectral)", 404

        # Read raw + rpl for this spectral cube
        try:
            backend_config = get_config()
            uploads_folder = backend_config["uploads-folder"]
            raw_name = matched.get("rawLocation")
            rpl_name = matched.get("rplLocation")
            raw_path = os.path.join(uploads_folder, data_source, raw_name)
            rpl_path = os.path.join(uploads_folder, data_source, rpl_name)

            info = parse_rpl(rpl_path)
            if not info:
                return "Failed to parse rpl file", 500
            width = int(info.get("width"))
            height = int(info.get("height"))
            depth = int(info.get("depth")) if info.get("depth") is not None else 0

            # Load full raw data
            dat = np.fromfile(raw_path, dtype=np.uint16)
            # reshape may fail if counts mismatch
            dat = np.reshape(dat, (height, width, depth))
            cube = np.transpose(dat, (2, 0, 1))
            is_elemental = False
        except Exception as e:
            LOG.error(f"Error reading spectral cube data: {e}")
            return "Failed to read spectral cube data", 500

    # Select layer if requested, otherwise compute summary
    try:
        if layer is not None:
            arr = cube[layer]
        else:
            arr = cube.sum(axis=0)
    except Exception as e:
        LOG.error(f"Error extracting layer from cube: {e}")
        return "Invalid layer index", 400

    # Normalize array
    try:
        image_array = normalize_ndarray_to_grayscale(arr)
    except Exception as e:
        LOG.error(f"Error normalizing array: {e}")
        return "Failed to normalize cube", 500

    # Build output filename
    if not output_name:
        output_name = f"grayscale_{cube_name}_{uuid.uuid4().hex[:8]}.png"

    # Save PNG to generated/uploads folder inside datasource folder
    try:
        backend_config = get_config()
        uploads_folder = backend_config["uploads-folder"]
        # get_path_to_generated_folder returns the full path to the generated folder for this data source
        generated_folder = get_path_to_generated_folder(data_source)
        if not generated_folder:
            LOG.error("Could not determine generated folder for data source %s", data_source)
            return "Failed to save image", 500
        if not os.path.isdir(generated_folder):
            os.makedirs(generated_folder, exist_ok=True)

        out_path = os.path.join(generated_folder, output_name)
        img = fromarray(image_array).convert("L")
        img.save(out_path)
    except Exception as e:
        LOG.error(f"Failed to save grayscale image: {e}")
        return "Failed to save image", 500

    # Build grayscale metadata entry
    entry_name = f"grayscale_{cube_name}"
    if not is_elemental:
        entry_name = f"grayscale_spectral_{cube_name}"

    grayscale_entry = {
        "name": entry_name,
        # imageLocation is stored relative to the data source, use generated folder name + filename
        "imageLocation": os.path.join(get_path_to_generated_folder(data_source).replace('\\', '/').split('/')[-1], output_name).replace("\\", "/"),
        "recipeLocation": "",
        # metadata to identify origin
        "sourceCubeName": cube_name,
        "sourceCubeType": "elemental" if is_elemental else "spectral"
    }

    # Update workspace.json to append grayscale entry
    try:
        workspace_path = get_path_to_workspace(data_source)
        if not workspace_path:
            return "Workspace not found", 404

        with open(workspace_path, "r+") as f:
            workspace = json.load(f)
            if "grayscale" not in workspace:
                workspace["grayscale"] = []
            workspace["grayscale"].append(grayscale_entry)
            f.seek(0)
            f.write(json.dumps(workspace))
            f.truncate()
    except Exception as e:
        LOG.error(f"Failed to update workspace with grayscale: {e}")
        return "Failed to update workspace", 500

    LOG.info(f"Created grayscale image for cube={cube_name}, saved as {output_name}, workspace updated")

    return grayscale_entry, 200
