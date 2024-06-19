from io import BytesIO
import logging

from PIL.Image import Image, fromarray
from flask import request, jsonify, abort, send_file
import numpy as np
from os.path import isfile, isdir
from os import rmdir
from os.path import exists, abspath, join
from os import mkdir
import json
from markupsafe import escape
from numpy import ndarray

from xrf_explorer import app
from xrf_explorer.server.file_system.helper import get_config
from xrf_explorer.server.file_system.workspace.contextual_images import (get_contextual_image_path,
                                                                         get_contextual_image_size,
                                                                         get_contextual_image,
                                                                         get_contextual_image_recipe_path)
from xrf_explorer.server.file_system.workspace.file_access import get_elemental_cube_recipe_path
from xrf_explorer.server.file_system.cubes.elemental import (
    normalize_ndarray_to_grayscale,
    get_elemental_map,
    get_element_names,
    get_short_element_names,
    get_element_averages,
    get_element_averages_selection,
    convert_elemental_cube_to_dms
)
from xrf_explorer.server.file_system.cubes.spectral import parse_rpl, get_spectra_params
from xrf_explorer.server.file_system.workspace.workspace_handler import get_path_to_workspace, update_workspace
from xrf_explorer.server.file_system.workspace.data_listing import get_data_sources_names, get_data_source_files
from xrf_explorer.server.file_system.workspace.file_access import (
    get_elemental_cube_path,
    get_raw_rpl_paths,
    get_base_image_name,
    get_workspace_dict
)
from xrf_explorer.server.image_register.register_image import load_points_dict
from xrf_explorer.server.process.dim_reduction import (
    generate_embedding,
    create_embedding_image,
    get_image_of_indices_to_embedding
)
from xrf_explorer.server.process.color_segmentation import (
    combine_bitmasks, get_clusters_using_k_means,
    get_elemental_clusters_using_k_means, merge_similar_colors,
    save_bitmask_as_png, convert_to_hex
)
from xrf_explorer.server.spectra import get_average_global, get_raw_data, get_average_selection, get_theoretical_data, bin_data
from xrf_explorer.server.image_to_cube_selection import get_selection, SelectionType, CubeType

LOG: logging.Logger = logging.getLogger(__name__)


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
    """Return a list of all available data sources stored in the data folder on the remote server as specified in the project's configuration.

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
    :return: If a GET request is made, the workspace content is sent as a json file. If a POST request is made, a confirmation message is sent.
    """

    if request.method == "POST":
        # Get send json file
        data: any = request.get_json()

        # Write content to the workspace
        result: bool = update_workspace(data_source, data)

        # Check if the write was successful
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

    if not config:
        error_msg: str = "Error occurred while creating data source directory"
        LOG.error(error_msg)
        return error_msg, 500

    if data_source == "":
        error_msg: str = "Data source name provided, but empty."
        LOG.error(error_msg)
        return error_msg, 400

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


@app.route("/api/<data_source>/abort", methods=["GET", "POST"])
def remove_data_source_dir(data_source: str):
    """Abort creation of a directory for a data source.

    :param data_source: The name of the data source to be aborted
    :return: json with directory name
    """
    # Get config
    config: dict | None = get_config()
    LOG.info(f"Aborting data source directory creation for {data_source}")

    if not config:
        error_msg: str = "Error occurred while removing data source directory"
        LOG.error(error_msg)
        return error_msg, 500

    if data_source == "":
        error_msg: str = "Data source name provided, but empty."
        LOG.error(error_msg)
        return error_msg, 400

    data_source_dir: str = join(config['uploads-folder'], data_source)

    if not isdir(data_source_dir):
        error_msg: str = "Data source name does not exist."
        LOG.error(error_msg)
        return error_msg, 400

    # remove data source dir
    LOG.info(f"Removing data source directory at {data_source_dir}")
    rmdir(data_source_dir)

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

    if not config:
        error_msg: str = "Error occurred while uploading file chunk"
        LOG.error(error_msg)
        return error_msg, 500

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
        succes: bool = convert_elemental_cube_to_dms(data_source, cube_name)
        if not succes:
            return "Error converting elemental data cube to .dms format", 500
        
    return "Converted elemental data cube to .dms format", 200


@app.route("/api/<data_source>/bin_raw/<bin_params>/", methods=["POST"])
def bin_raw_data(data_source: str, bin_params: str):
    """Bins the raw data files channels to compress the file.

    :param data_source: the data source containing the raw data to bin.
    :param bin_params: the JSON list of parameters: low, high, binSize.
    :return: A boolean indicating if the binning was successful.
    """
    params: dict = json.loads(bin_params)
    low: int = params["low"]
    high: int = params["high"]
    bin_size: int = params["binSize"]

    try:
        bin_data(data_source, low, high, bin_size)
        LOG.info("binned")
    except Exception as e:
        LOG.error("error while loading raw file: {%s}", e)

    return "Binned data", 200


@ app.route("/api/<data_source>/element_averages", methods=["POST", "GET"])
def list_element_averages(data_source: str):
    """Get the names and averages of the elements present in the painting.

    :param data_source: data_source to get the element averages from
    :return: JSON list of objects indicating average abundance for every element. Each object is of the form {name: element name, average: element abundance}
    """

    path: str | None = get_elemental_cube_path(data_source)

    if path is None:
        return "Error occurred while getting elemental datacube path", 500

    composition: list[dict[str, str | float]] = get_element_averages(path)
    try:
        return json.dumps(composition)
    except Exception as e:
        LOG.error(f"Failed to serialize element averages: {str(e)}")
        return "Error occurred while listing element averages", 500


@app.route("/api/<data_source>/element_averages_selection", methods=["POST"])
def list_element_averages_selection(data_source: str):
    """Get the names and averages of the elements present in a rectangular selection
    of the painting.

    :param data_source: data_source to get the element averages from
    :return: JSON list of objects indicating average abundance for every element.
Each object is of the form {name: element name, average: element abundance}
    """
    # path to elemental cube
    path: str | None = get_elemental_cube_path(data_source)

    if path is None:
        return "Error getting elemental datacube path", 500

    # parse JSON payload
    data: dict[str, str] | None = request.get_json()
    if data is None:
        return "Error parsing request body", 400

    # get selection type and points
    selection_type: str | None = data.get('type')
    points: list[dict[str, float]] | None = data.get('points')

    if selection_type is None or points is None:
        return "Error occurred while getting selection type or points from request body", 400

    # validate and parse selection type
    try:
        selection_type_parsed: SelectionType = SelectionType(selection_type)
    except ValueError:
        return "Error parsing selection type", 400

    # validate and parse points
    if not isinstance(points, list):
        return "Error parsing points; expected a list of points", 400

    try:
        points_parsed: list[tuple[int, int]] = [
            (round(point['x']), round(point['y'])) for point in points
        ]
    except ValueError:
        return "Error parsing points", 400

    # get selection
    mask: np.ndarray | None = get_selection(
        data_source, points_parsed, selection_type_parsed, CubeType.Elemental
    )

    if mask is None:
        return "Error occurred while getting selection from datacube", 500

    # get names
    names: list[str] = get_short_element_names(path)

    # get averages
    composition: list[dict[str, str | float]] = get_element_averages_selection(path, mask, names)

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
    path: str | None = get_elemental_cube_path(data_source)

    if path is None:
        return "Error getting elemental datacube path", 500

    names: list[str] = get_element_names(path)
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
    :return: string code indicating the status of the embedding generation. "success" when embedding was generated successfully, "downsampled" when successful and the number of data points was down sampled.
    """

    # Try to generate the embedding
    result = generate_embedding(data_source, element, threshold, request.args)
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
    """Creates the image for lasso selection that decodes to which points in the embedding
    the pixels of the elemental data cube are mapped. Uses the current embedding and indices
    for the given data source to create the image.

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

    # As XRF-Explorer only supports a single data cube, we take the size of the first spectral cube
    _, path = get_raw_rpl_paths(data_source)

    # Parse the .rpl file
    rpl_data = parse_rpl(path)

    # Return the width and height
    return {
        "width": rpl_data["width"],
        "height": rpl_data["height"]
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
def get_element_spectra(data_source: str, element: str, excitation: int):
    """Compute the theoretical spectrum in channel range [low, high] for an element with a bin size, as well as the element's peaks energies and intensity.

    :param data_source: the name of the data source, used for getting the spectrum boundaries and bin size.
    :param element: the chemical element to get the theoretical spectra of.
    :param excitation: the excitation energy.
    :return: json list of tuples containing the bin number and the theoretical intensity for this bin, the peak energies and the peak intensities.
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
        element, int(excitation), low, high, bin_size)

    response = json.dumps(response)

    return response


@app.route('/api/<data_source>/get_selection_spectrum', methods=['POST'])
def get_selection_spectra(data_source: str):
    """Get the average spectrum of the selected pixels of a rectangle selection.

    :param data_source: the name of the data source
    :return: json list of tuples containing the channel number and the average intensity of this channel.
    """

    selection: dict[str, any] | None = request.get_json()
    if selection is None:
        return "Error parsing request body", 400
    
    # get selection type and points
    selection_type: str | None = selection.get('type')
    points: list[dict[str, float]] | None = selection.get('points')
    if selection_type is None or points is None:
        return "Error occurred while getting selection type or points from request body", 400
    
    # validate and parse selection type
    try:
        selection_type_parsed: SelectionType = SelectionType(selection_type)
    except ValueError:
        return "Error parsing selection type", 400
    
    # validate and parse points
    if not isinstance(points, list):
        return "Error parsing points; expected a list of points", 400
    try:
        points_parsed: list[tuple[int, int]] = [(round(point['x']), round(point['y'])) for point in points]
    except ValueError:
        return "Error parsing points", 400
    
    # get selection
    mask: np.ndarray | None = get_selection(data_source, points_parsed, selection_type_parsed, CubeType.Raw)
    if mask is None:
        return "Error occurred while getting selection from datacube", 500

    # get average
    result = get_average_selection(data_source, mask)
    try:
        return json.dumps(result)
    except Exception as e:
        LOG.error(f"Failed to serialize element averages: {str(e)}")
        return "Error occurred while listing element averages", 500


@app.route('/api/<data_source>/cs/clusters', methods=['GET'])
def get_color_clusters(data_source: str):
    """Gets the colors corresponding to the image-wide color clusters, and saves the
    corresponding bitmasks.

    :param data_source: data_source to get the clusters from
    :return json containing the ordered list of colors
    """
    # Get rgb image name and path
    rgb_image_name: str = get_base_image_name(data_source)
    if rgb_image_name is None:
        return 'Error occurred while getting rgb image name', 500
    path_to_image: str = get_contextual_image_path(data_source, rgb_image_name)
    if path_to_image is None:
        return 'Error occurred while getting rgb image path', 500

    config: dict | None = get_config()
    if not config:
        return 'Error occurred while getting backend config', 500
    uploads_folder: str = str(config['uploads-folder'])
    cs_folder: str = str(config['color-segmentation']['folder-name'])

    # Paths
    path_to_data_cube: str = get_elemental_cube_path(data_source)
    if not path_to_data_cube:
        return f"Could not find elemental data cube in source {data_source}", 500
    path_to_save: str = join(uploads_folder, data_source, cs_folder)

    # get default dim reduction config for image clusters
    k_means_parameters: dict[str,
                             str] = config['color-segmentation']['k-means-parameters']
    nr_attempts: int = int(k_means_parameters['nr-attempts'])
    k: int = int(k_means_parameters['k'])

    # get default dim reduction config for elemental clusters
    k_means_parameters_elem: dict[str,
                                  str] = config['color-segmentation']['elemental-k-means-parameters']
    elem_threshold: float = float(k_means_parameters_elem['elem-threshold'])
    nr_attempts_elem: int = int(k_means_parameters_elem['nr-attempts'])
    k_elem: int = int(k_means_parameters_elem['k'])

    # path to json for caching
    full_path_json: str = join(path_to_save,
                               f'colors_{k}_{nr_attempts}_{elem_threshold}_{k_elem}_{nr_attempts_elem}.json')
    # If json already exists, return that directly
    if exists(full_path_json):
        with open(full_path_json, 'r') as json_file:
            color_data: ndarray = json.load(json_file)
        return jsonify(color_data)

    # Create directory if it doesn't exist
    if not exists(path_to_save):
        mkdir(path_to_save)

    # List to store colors
    color_data: list[ndarray] = []

    # Compute colors and bitmasks
    colors: ndarray
    bitmasks: ndarray
    colors, bitmasks = get_clusters_using_k_means(
        data_source, rgb_image_name, nr_attempts, k)
    # Merge similar clusters
    colors, bitmasks = merge_similar_colors(colors, bitmasks)
    # Combine bitmasks into one
    combined_bitmask: ndarray = combine_bitmasks(bitmasks)

    # Save bitmask
    full_path: str = join(path_to_save, f'imageClusters_{k}_{nr_attempts}.png')
    image_saved: bool = save_bitmask_as_png(combined_bitmask, full_path)
    if not image_saved:
        return 'Error occurred while saving bitmask as png', 500

    # Store colors
    color_data.append(convert_to_hex(colors))

    # Compute colors and bitmasks per element
    colors_per_elem: ndarray
    bitmasks_per_elem: ndarray
    colors_per_elem, bitmasks_per_elem = get_elemental_clusters_using_k_means(
        data_source, rgb_image_name, elem_threshold, nr_attempts_elem, k_elem
    )

    for i in range(len(colors_per_elem)):
        # Merge similar clusters
        colors_per_elem[i], bitmasks_per_elem[i] = merge_similar_colors(
            colors_per_elem[i], bitmasks_per_elem[i])
        color_data.append(convert_to_hex(colors_per_elem[i]))

        # Stored combined bitmask and colors
        combined_bitmask: ndarray = combine_bitmasks(bitmasks_per_elem[i])

        # Save bitmask
        full_path: str = join(path_to_save,
                              f'elementCluster_{i}_{elem_threshold}_{k_elem}_{nr_attempts_elem}.png')
        image_saved: bool = save_bitmask_as_png(combined_bitmask, full_path)
        if not image_saved:
            return f'Error occurred while saving bitmask for element {i} as png', 500

    # cache data
    with open(full_path_json, 'w') as json_file:
        json.dump(color_data, json_file)

    return json.dumps(color_data)


@ app.route('/api/<data_source>/cs/image/bitmask', methods=['GET'])
def get_color_cluster_bitmask(data_source: str):
    """
    Returns the png bitmask for the color clusters over the whole painting.

    :param data_source: data_source to get the bitmask from
    :return bitmask png file for the whole image
    """
    config: dict | None = get_config()
    if not config:
        return 'Error occurred while getting backend config', 500
    uploads_folder: str = str(config['uploads-folder'])
    cs_folder: str = str(config['color-segmentation']['folder-name'])

    # Get parameters
    k_means_parameters: dict[str,
                             str] = config['color-segmentation']['k-means-parameters']
    nr_attempts: int = int(k_means_parameters['nr-attempts'])
    k: int = int(k_means_parameters['k'])

    # Get path to image
    path_to_save: str = join(uploads_folder, data_source, cs_folder)
    full_path: str = join(path_to_save, f'imageClusters_{k}_{nr_attempts}.png')
    # If image doesn't exist, compute clusters
    if not exists(full_path):
        get_color_clusters(data_source)

    return send_file(abspath(full_path), mimetype='image/png')


@app.route('/api/<data_source>/cs/element/<int:element>/bitmask', methods=['GET'])
def get_element_color_cluster_bitmask(data_source: str, element: int):
    """
    Returns, for the requested element, the png bitmask for the color clusters.

    :param data_source: data_source to get the bitmask from
    :param element: index of the element to get the bitmask from
    :return bitmask png file for the given element
    """
    config: dict = get_config()
    uploads_folder: str = str(config['uploads-folder'])
    cs_folder: str = str(config['color-segmentation']['folder-name'])

    # Get parameters
    k_means_parameters: dict[str,
                             str] = config['color-segmentation']['elemental-k-means-parameters']
    elem_threshold: float = float(k_means_parameters['elem-threshold'])
    nr_attempts: int = int(k_means_parameters['nr-attempts'])
    k: int = int(k_means_parameters['k'])

    # Path to bitmask
    path_to_save: str = join(uploads_folder, data_source, cs_folder)
    full_path: str = join(path_to_save,
                          f'elementCluster_{element}_{elem_threshold}_{k}_{nr_attempts}.png')
    if not exists(full_path):
        get_color_clusters(data_source)

    return send_file(abspath(full_path), mimetype='image/png')
