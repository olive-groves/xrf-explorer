import json
import logging

from io import BytesIO
from os import rmdir, mkdir, unlink, listdir
from os.path import isfile, isdir, exists, abspath, join
from shutil import rmtree

import numpy as np

from PIL.Image import Image, fromarray
from flask import request, jsonify, abort, send_file
from markupsafe import escape

from xrf_explorer import app

from xrf_explorer.server.color_segmentation import (
    get_path_to_cs_folder,
    combine_bitmasks,
    get_clusters_using_k_means,
    get_elemental_clusters_using_k_means,
    save_bitmask_as_png,
    convert_to_hex
)
from xrf_explorer.server.dim_reduction import (
    generate_embedding,
    create_embedding_image,
    get_image_of_indices_to_embedding
)
from xrf_explorer.server.image_register import load_points_dict
from xrf_explorer.server.image_to_cube_selection import get_selection, SelectionType, CubeType

from xrf_explorer.server.file_system import get_config
from xrf_explorer.server.file_system.cubes import (
    normalize_ndarray_to_grayscale,
    get_elemental_datacube_dimensions,
    get_elemental_map,
    get_element_names,
    get_element_averages,
    get_element_averages_selection,
    convert_elemental_cube_to_dms,
    get_spectra_params,
    update_bin_params,
    parse_rpl,
    bin_data
)
from xrf_explorer.server.file_system.sources import get_data_sources_names, get_data_source_files
from xrf_explorer.server.file_system.workspace import (
    get_contextual_image_path,
    get_contextual_image_size,
    get_contextual_image,
    get_contextual_image_recipe_path,
    get_path_to_workspace,
    update_workspace,
    get_workspace_dict,
    get_elemental_cube_path,
    get_elemental_cube_recipe_path,
    get_base_image_name, get_raw_rpl_paths
)

from xrf_explorer.server.spectra import (
    get_average_global,
    get_raw_data,
    get_average_selection,
    get_theoretical_data
)

LOG: logging.Logger = logging.getLogger(__name__)


def validate_data_source(data_source_name: str) -> tuple[str, int] | None:
    if data_source_name == "":
        error_msg: str = "Data source name provided, but empty."
        LOG.error(error_msg)
        return error_msg, 400
    return None


def validate_config(config: dict | None) -> tuple[str, int] | None:
    if not config:
        error_msg: str = "Error occurred while getting backend config"
        LOG.error(error_msg)
        return error_msg, 500
    return None


def parse_selection(selection_data: dict[str: str]) -> tuple[SelectionType, list[tuple[int, int]]] | tuple[str, int]:
    # get selection type and points
    selection_type: str | None = selection_data.get('type')
    points: list[dict[str, float]] | None = selection_data.get('points')
    if selection_type is None or points is None:
        return "Error occurred while getting selection type or points from request body", 400

    # validate and parse selection type
    try:
        selection_type_parsed: SelectionType = SelectionType(selection_type)
    except ValueError:
        return "Error parsing selection type", 400

    # validate and parse points
    if not isinstance(points, list):
        return f"Error parsing points: expected a list of points, got {type(points)}", 400
    try:
        points_parsed: list[tuple[int, int]] = [(round(point['x']), round(point['y'])) for point in points]
    except ValueError:
        return "Error parsing points", 400

    return selection_type_parsed, points_parsed


@app.route("/api")
def api():
    """Returns a list of all api endpoints.

    :return: list of api endpoints
    """

    routes: list[str] = []

    for rule in app.url_map.iter_rules():
        if rule.rule.startswith("/api"):
            routes.append(rule.rule)

    routes.sort()

    return routes


@app.route("/api/datasources")
def list_accessible_data_sources():
    """Return a list of all available data sources stored in the data folder on the remote server as specified in the
    project's configuration.

    :return: json list of strings representing the data sources names
    """
    try:
        return json.dumps(get_data_sources_names())
    except Exception as e:
        LOG.error(f"Failed to serialize files: {str(e)}")
        return "Error occurred while listing data sources", 500


@app.route("/api/<data_source>/workspace", methods=["GET", "POST"])
def get_workspace(data_source: str):
    """ Gets the workspace content for the specified data source or writes to it if a POST request is made.

    :param data_source: The name of the data source to get the workspace content for
    :return: If a GET request is made, the workspace content is sent as a json file. If a POST request is made, a confirmation message is sent
    """

    if request.method == "POST":
        # Get send json file
        data: any = request.get_json()

        # Write content to the workspace
        result: bool = update_workspace(data_source, data)

        # Check if writing was successful
        if not result:
            abort(400)

        return f"Data written to workspace {escape(data_source)} successfully"
    else:
        # Read content from the workspace
        path: str = get_path_to_workspace(data_source)

        # Check if the workspace exists
        if not path:
            abort(404)

        # Send the json file
        return send_file(abspath(path), mimetype='application/json')


@app.route("/api/<data_source>/files")
def datasource_files(data_source: str):
    """Return a list of all available files for a data source.

    :param data_source: The name of the data source to get the files for
    :return: json list of strings representing the file names
    """
    try:
        return json.dumps(get_data_source_files(data_source))
    except Exception as e:
        LOG.error(f"Failed to serialize files: {str(e)}")
        return "Error occurred while listing files", 500


@app.route("/api/<data_source>/create", methods=["POST"])
def create_data_source_dir(data_source: str):
    """Create a directory for a new data source.

    :param data_source: The name of the data source to create
    :return: json with directory name
    """
    # Get config
    config: dict | None = get_config()

    error_response_config: tuple[str, int] | None = validate_config(config)
    if error_response_config:
        return error_response_config

    error_response_ds: tuple[str, int] | None = validate_data_source(data_source)
    if error_response_ds:
        return error_response_ds

    if data_source in get_data_sources_names():
        error_msg: str = "Data source name already exists."
        LOG.error(error_msg)
        return error_msg, 400

    data_source_dir = join(config["uploads-folder"], data_source)

    # create data source dir
    if not isdir(data_source_dir):
        LOG.info(f"Creating data source directory at {data_source_dir}")
        mkdir(data_source_dir)

    return jsonify({"dataSourceDir": data_source})


@app.route("/api/<data_source>/remove", methods=["POST"])
def remove_data_source(data_source: str):
    """Removes workspace.json from a data source,

    :param data_source: The name of the data source to be aborted
    :return: json with directory name
    """
    # Get config
    config: dict | None = get_config()
    LOG.info(f"Aborting data source directory creation for {data_source}")

    error_resonse_config: tuple[str, int] | None = validate_config(config)
    if error_resonse_config:
        return error_resonse_config

    error_response_ds: tuple[str, int] | None = validate_data_source(data_source)
    if error_response_ds:
        return error_response_ds

    data_source_path: str = join(config['uploads-folder'], data_source)
    workspace_path: str = join(data_source_path, "workspace.json")
    generated_path: str = join(data_source_path, "generated")

    if isdir(generated_path):
        # remove generated files
        rmtree(generated_path)

    if isfile(workspace_path):
        # remove workspace.json
        LOG.info(f"Removing workspace.json at {workspace_path}")
        unlink(workspace_path)

    if isdir(data_source_path) and len(listdir(data_source_path)) == 0:
        # remove directory if it is empty
        rmdir(data_source_path)

    return jsonify({"dataSourceDir": data_source})


@app.route("/api/<data_source>/delete", methods=["DELETE"])
def delete_data_source(data_source: str):
    """Completely deletes and removes all files from data source.
    
    :param data_source: The data source to delete.
    :return: json with directory name
    """
    # Get config
    config: dict | None = get_config()
    LOG.info(f"Aborting data source directory creation for {data_source}")

    error_response_ds: tuple[str, int] | None = validate_data_source(data_source)
    if error_response_ds:
        return error_response_ds

    data_source_dir: str = join(config['uploads-folder'], data_source)

    if not isdir(data_source_dir):
        error_msg: str = "Data source name does not exist."
        LOG.error(error_msg)
        return error_msg, 400

    # remove data source dir
    LOG.info(f"Removing data source directory at {data_source_dir}")
    rmtree(data_source_dir)

    return jsonify({"dataSourceDir": data_source})


@app.route("/api/<data_source>/upload/<file_name>/<int:start>", methods=["POST"])
def upload_chunk(data_source: str, file_name: str, start: int):
    """Upload a chunk of bytes to a file in specified data source.

    :param data_source: The name of the data source to upload the chunk to
    :param file_name: The name of the file to upload the chunk to
    :param start: The start index of the chunk in the specified file
    """

    # get config
    config: dict | None = get_config()

    error_resonse_config: tuple[str, int] | None = validate_config(config)
    if error_resonse_config:
        return error_resonse_config

    # get file location
    path: str = abspath(join(config['uploads-folder'], data_source, file_name))

    # test that path is a sub path of the uploads-folder
    if not path.startswith(abspath(join(config['uploads-folder'], data_source))):
        LOG.info("Attempted to upload chunk to %s which is not allowed", path)
        return "Unauthorized file chunk location", 401

    # create file if it does not exist
    if not isfile(path):
        LOG.info("Created file %s", path)
        open(path, "x+b").close()

    # write chunk to file
    with open(path, "r+b") as file:
        file.seek(start)
        file.write(request.get_data())
        LOG.info("Wrote chunk from %i into %s", start, path)

    return "Uploaded file chunk", 200


@app.route("/api/<data_source>/data/convert")
def convert_elemental_cube(data_source: str):
    """Converts all elemental data cubes of a data source to .dms format.

    :param data_source: The name of the data source to convert the elemental data cube
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


@app.route("/api/<data_source>/bin_raw/", methods=["POST"])
def bin_raw_data(data_source: str):
    """Bins the raw data files channels to compress the file.

    :param data_source: the data source containing the raw data to bin
    :return: A boolean indicating if the binning was successful
    """
    try:
        params: dict = get_spectra_params(data_source)
    except FileNotFoundError as err:
        return f"error while loading workspace to retrieve spectra params: {str(err)}", 500
    
    binned: bool = params["binned"]
    
    if not binned:
        try:
            update_bin_params(data_source)
            params: dict = get_spectra_params(data_source)
            low: int = params["low"]
            high: int = params["high"]
            bin_size: int = params["binSize"]
            
            bin_data(data_source, low, high, bin_size)
            LOG.info("binned")
            return "Binned data", 200
        
        except FileNotFoundError as err:
            return f"error while loading workspace to retrieve spectra params: {str(err)}", 5000
    else:
        return "Data already binned", 200


@app.route("/api/<data_source>/get_offset", methods=["GET"])
def get_offset(data_source: str):
    """Returns the depth offset energy of the raw data, that is the energy level of channel 0.
    
    :param data_source: the data source containing the raw data
    :return: The depth offset
    """
    _, path_to_rpl = get_raw_rpl_paths(data_source)

    # get dimensions from rpl file
    info = parse_rpl(path_to_rpl)
    if not info:
        return np.empty(0)

    try:
        return json.dumps(float(info['depthscaleorigin']))
    except Exception:
        # If we can't get the offset, set default values
        return json.dumps(0)


@app.route("/api/<data_source>/element_averages", methods=["POST", "GET"])
def list_element_averages(data_source: str):
    """Get the names and averages of the elements present in the painting.

    :param data_source: data_source to get the element averages from
    :return: JSON list of objects indicating average abundance for every element. Each object is of the form {name: element name, average: element abundance}
    """
    composition: list[dict[str, str | float]] = get_element_averages(data_source)

    try:
        return json.dumps(composition)
    except Exception as e:
        LOG.error(f"Failed to serialize element averages: {str(e)}")
        return "Error occurred while listing element averages", 500


@app.route("/api/<data_source>/element_averages_selection", methods=["POST"])
def list_element_averages_selection(data_source: str):
    """Get the names and averages of the elements present in a rectangular selection of the painting.

    :param data_source: data_source to get the element averages from
    :return: JSON list of objects indicating average abundance for every element. Each object is of the form {name: element name, average: element abundance}
    """
    # parse JSON payload
    selection: SelectionType
    points: list[tuple[int, int]]
    selection, points = parse_selection(request.get_json())

    # get selection
    mask: np.ndarray | None = get_selection(data_source, points, selection, CubeType.Elemental)

    if mask is None:
        return "Error occurred while getting selection from datacube", 500

    # get averages
    composition: list[dict[str, str | float]] = get_element_averages_selection(data_source, mask)

    try:
        return json.dumps(composition)
    except Exception as e:
        LOG.error(f"Failed to serialize element averages: {str(e)}")
        return "Error occurred while listing element averages", 500


@app.route("/api/<data_source>/data/elements/names")
def list_element_names(data_source: str):
    """Get the short names of the elements stored in the elemental data cube.

    :param data_source: data source to get the element names from
    :return: JSON list of the short names of the elements.
    """
    names: list[str] = get_element_names(data_source)
    try:
        return json.dumps(names)
    except Exception as e:
        LOG.error(f"Failed to serialize element names: {str(e)}")
        return "Error occurred while listing element names", 500


@app.route("/api/<data_source>/dr/embedding/<int:element>/<int:threshold>")
def get_dr_embedding(data_source: str, element: int, threshold: int):
    """Generate the dimensionality reduction embedding of an element, given a threshold.

    :param data_source: data source to generate the embedding from
    :param element: element to generate the embedding for
    :param threshold: threshold from which a pixel is selected
    :return: string code indicating the status of the embedding generation.
             "success" when embedding was generated successfully,
             "downsampled" when successful and the number of data points was down sampled.
    """
    scaled_threshold: int = int(255 * threshold / 100)
    # Try to generate the embedding
    result = generate_embedding(data_source, element, scaled_threshold, request.args)
    if result == "success" or result == "downsampled":
        return result

    error_msg: str = "Failed to create DR embedding image"
    LOG.error(error_msg)
    return error_msg, 400


@app.route("/api/<data_source>/dr/overlay/<overlay_type>")
def get_dr_overlay(data_source: str, overlay_type: str):
    """Generate the dimensionality reduction overlay with a given type.

    :param data_source: data source to get the overlay from
    :param overlay_type: the overlay type. Images are prefixed with contextual_ and elements by elemental_
    :return: overlay image file
    """

    # Try to get the embedding image
    image_path: str = create_embedding_image(data_source, overlay_type)
    if not image_path:
        error_msg: str = "Failed to create DR embedding image"
        LOG.error(error_msg)
        return error_msg, 400

    return send_file(abspath(image_path), mimetype='image/png')


@app.route("/api/<data_source>/dr/embedding/mapping")
def get_dr_embedding_mapping(data_source: str):
    """Creates the image for polygon selection that decodes to which points in the embedding the pixels of the elemental
    data cube are mapped. Uses the current embedding and indices for the given data source to create the image.

    :param data_source: data source to get the overlay from
    :return: image that decodes to which points in the embedding the pixels of the elemental data cube are mapped
    """

    # Try to get the image
    image_path: str = get_image_of_indices_to_embedding(data_source)
    if not image_path:
        error_msg: str = "Failed to create DR indices to embedding image"
        LOG.error(error_msg)
        return error_msg, 400

    return send_file(abspath(image_path), mimetype='image/png')


@app.route("/api/<data_source>/image/<name>")
def contextual_image(data_source: str, name: str):
    """Get a contextual image.

    :param data_source: data source to get the image from
    :param name: the name of the image in workspace.json
    :return: the contextual image converted to png
    """

    path: str | None = get_contextual_image_path(data_source, name)
    if path is None:
        return f"Image {name} not found in source {data_source}", 404

    LOG.info("Opening contextual image")

    image: Image | None = get_contextual_image(path)
    if image is None:
        return f"Failed to open image {name} from source {data_source}", 500

    LOG.info("Converting contextual image")

    image_io = BytesIO()
    image.save(image_io, "png")
    image_io.seek(0)

    LOG.info("Serving converted contextual image")

    # Ensure that the converted images are cached by the client
    response = send_file(image_io, mimetype='image/png')
    response.headers["Cache-Control"] = "public, max-age=604800, immutable"
    return response


@app.route("/api/<data_source>/image/<name>/size")
def contextual_image_size(data_source: str, name: str):
    """Get the size of a contextual image.

    :param data_source: data source to get the image from
    :param name: the name of the image in workspace.json
    :return: the size of the contextual image
    """

    path: str | None = get_contextual_image_path(data_source, name)
    if not path:
        return f"Image {name} not found in source {data_source}", 404

    size = get_contextual_image_size(path)
    if not size:
        return f"Failed to get size of image {name} from source {data_source}", 500

    return {
        "width": size[0],
        "height": size[1]
    }


@app.route("/api/<data_source>/image/<name>/recipe")
def contextual_image_recipe(data_source: str, name: str):
    """Get the registering recipe of a contextual image.

    :param data_source: data source to get the image recipe from
    :param name: the name of the image in workspace.json
    :return: the registering recipe of the contextual image
    """

    path: str | None = get_contextual_image_recipe_path(data_source, name)
    if not path:
        return f"Could not find recipe for image {name} in source {data_source}", 404

    # Get the recipe points
    points: dict = load_points_dict(path)
    if not points:
        return f"Could not find registering points at {path}", 404

    return points, 200


@app.route("/api/<data_source>/data/size")
def data_cube_size(data_source: str):
    """Get the size of the data cubes.


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
    """Get the registering recipe for the data cubes.

    :param data_source: data source to get the recipe from
    :return: the registering recipe of the data cubes
    """

    # As XRF-Explorer only supports a single data cube, we take the recipe of the first elemental cube
    path: str | None = get_elemental_cube_recipe_path(data_source)
    if not path:
        return f"Could not find recipe for data cubes in source {data_source}", 404

    # Get the recipe points
    points: dict = load_points_dict(path)
    if not points:
        return f"Could not find registering points at {path}", 404

    return points, 200


@app.route("/api/<data_source>/data/elements/map/<int:channel>")
def elemental_map(data_source: str, channel: int):
    """Get an elemental map.

    :param data_source: data source to get the map from
    :param channel: the channel to get the map from
    :return: the elemental map
    """

    # As XRF-Explorer only supports a single data cube, we do not have to do any wizardry to stitch maps together
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


@app.route('/api/<data_source>/get_average_data', methods=['GET'])
def get_average_data(data_source: str):
    """Computes the average of the raw data for each bin of channels in range [low, high] on the whole painting.

    :return: json list of tuples containing the bin number and the average intensity for this bin
    """
    datacube: np.ndarray = get_raw_data(data_source)

    average_values: list = get_average_global(datacube)
    response = json.dumps(average_values)

    return response


@app.route('/api/<data_source>/get_element_spectrum/<element>/<excitation>', methods=['GET'])
def get_element_spectra(data_source: str, element: str, excitation: float):
    """Compute the theoretical spectrum in channel range [low, high] for an element with a bin size, as well as the
    element's peaks energies and intensity.

    :param data_source: the name of the data source, used for getting the spectrum boundaries and bin size
    :param element: the chemical element to get the theoretical spectra of
    :param excitation: the excitation energy
    :return: json list of tuples containing the bin number and the theoretical intensity for this bin, the peak energies and the peak intensities
    """
    try:
        params: dict[str, int] = get_spectra_params(data_source)
    except FileNotFoundError:
        return "error while loading workspace to retrieve spectra params: {%s}", 404

    if params is None:
        return "Error occurred while loading element spectrum", 404

    low: int = params["low"]
    high: int = params["high"]
    bin_size: int = params["binSize"]
    response = get_theoretical_data(
        element, float(excitation), low, high, bin_size)

    response = json.dumps(response)

    return response


@app.route('/api/<data_source>/get_selection_spectrum', methods=['POST'])
def get_selection_spectra(data_source: str):
    """Get the average spectrum of the selected pixels of a rectangle selection.

    :param data_source: the name of the data source
    :return: JSON array where the index is the channel number and the value is the average intensity of that channel
    """

    # parse JSON payload
    selection: SelectionType
    points: list[tuple[int, int]]
    selection, points = parse_selection(request.get_json())

    # get selection
    mask: np.ndarray | None = get_selection(data_source, points, selection, CubeType.Raw)
    if mask is None:
        return "Error occurred while getting selection from datacube", 500

    # get average
    result: list[float] = get_average_selection(data_source, mask)
    try:
        return json.dumps(result)
    except Exception as e:
        LOG.error(f"Failed to serialize element averages: {str(e)}")
        return "Error occurred while listing element averages", 500


@app.route('/api/<data_source>/cs/clusters/<int:elem>/<int:k>/<int:elem_threshold>', methods=['GET'])
def get_color_clusters(data_source: str, elem: int, k: int, elem_threshold: int):
    """Gets the colors corresponding to the image-wide/element-wise color clusters, and caches them as well as the
    corresponding bitmasks.

    :param data_source: data_source to get the clusters from
    :param elem: index of selected element (0 if whole painting, channel+1 if element)
    :param k: number of color clusters to compute
    :param elem_threshold: elemental threshold
    :return json containing the ordered list of colors
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
    """Returns the png bitmask for the color clusters over the whole painting/selected element.

    :param data_source: data_source to get the bitmask from
    :param elem: index of selected element (0 if whole painting, channel+1 if element)
    :param k: number of color clusters to compute
    :param elem_threshold: elemental threshold
    :return bitmask png file for the whole image
    """
    LOG.info(f'Bitmasks for k={k}, elem={elem}, elme_Threshold={elem_threshold}')
    config: dict | None = get_config()

    error_resonse_config: tuple[str, int] | None = validate_config(config)
    if error_resonse_config:
        return error_resonse_config

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
