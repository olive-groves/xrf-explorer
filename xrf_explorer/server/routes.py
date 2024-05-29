import logging
import json

from flask import request, jsonify, abort, send_file
from werkzeug.utils import secure_filename
from os.path import exists, join, abspath
from os import mkdir
from shutil import rmtree
from markupsafe import escape
from numpy import ndarray

from xrf_explorer import app
from xrf_explorer.server.file_system.config_handler import load_yml
from xrf_explorer.server.file_system.workspace_handler import get_path_to_workspace, update_workspace
from xrf_explorer.server.file_system.data_listing import get_data_sources_names
from xrf_explorer.server.file_system import get_short_element_names, get_element_averages
from xrf_explorer.server.dim_reduction.embedding import generate_embedding
from xrf_explorer.server.dim_reduction.overlay import create_embedding_image
from xrf_explorer.server.spectra import *
from xrf_explorer.server.color_seg import (
    get_image, combine_bitmasks, get_clusters_using_k_means,
    get_elemental_clusters_using_k_means, merge_similar_colors,
    save_bitmask_as_png
)

LOG: logging.Logger = logging.getLogger(__name__)
CONFIG_PATH: str = 'config/backend.yml'
BACKEND_CONFIG: dict = load_yml(CONFIG_PATH)

TEMP_ELEMENTAL_CUBE: str = '196_1989_M6_elemental_datacube_1069_1187_rotated_inverted.dms'


@app.route("/api")
def api():
    return "this is where the API is hosted"


@app.route("/api/info")
def info():
    return "adding more routes is quite trivial"


@app.route("/api/available_data_sources")
def list_accessible_data_sources():
    try:
        return json.dumps(get_data_sources_names())
    except Exception as e:
        LOG.error(f"Failed to serialize files: {str(e)}")
        return "Error occurred while listing data sources", 500


@app.route("/api/workspace/<datasource>", methods=["GET", "POST"])
def get_workspace(datasource: str):
    """ Gets the workspace content for the specified data source or writes to it if a POST request is made.

    :param datasource: The name of the data source to get the workspace content for
    :return: If a GET request is made, the workspace content is sent as a json file. If a POST request is made, a confirmation message is sent.
    """

    if request.method == "POST":
        # Get send json file
        data: any = request.get_json()

        # Write content to the workspace
        result: bool = update_workspace(datasource, data)
        
        # Check if the write was successful
        if not result:
            abort(400)
        
        return f"Data written to workspace {escape(datasource)} successfully"
    else:
        # Read content from the workspace
        path: str = get_path_to_workspace(datasource)

        # Check if the workspace exists
        if not path:
            abort(404)
        
        # Send the json file
        return send_file(abspath(path), mimetype='application/json')


@app.route("/api/create_ds_dir", methods=["POST"])
def create_data_source_dir():
    # Check the 'name' field was provided in the request
    if "name" not in request.form:
        error_msg = "Data source name must be provided."
        LOG.error(error_msg)
        return error_msg, 400

    data_source_name = request.form["name"].strip()
    data_source_name_secure = secure_filename(data_source_name)

    if data_source_name == "":
        error_msg = "Data source name provided, but empty."
        LOG.error(error_msg)
        return error_msg, 400

    data_source_dir = join(BACKEND_CONFIG["uploads-folder"], data_source_name_secure)

    # If the directory exists, return 400
    if exists(data_source_dir):
        error_msg = "Data source name already exists."
        LOG.error(error_msg)
        return error_msg, 400

    # create data source dir
    mkdir(data_source_dir)

    LOG.info(f"Data source directory created at {data_source_dir}")

    return jsonify({"dataSourceDir": data_source_name_secure})


@app.route("/api/delete_data_source", methods=["DELETE"])
def delete_data_source():
    delete_dir = join(BACKEND_CONFIG["uploads-folder"], request.form["dir"])

    if exists(delete_dir):
        rmtree(delete_dir)
        LOG.info(f"Data source at {delete_dir} removed.")
        return "Deleted", 200
    else:
        return "Directory not found", 404


@app.route("/api/upload_file_chunk", methods=["POST"])
def upload_file_chunk():
    file_dir = join(BACKEND_CONFIG["uploads-folder"], request.form["dir"])
    start_byte = int(request.form["startByte"])
    chunk_bytes = request.files["chunkBytes"]

    # If the file does not exist, create it
    if not exists(file_dir):
        open(file_dir, "w+b").close()

    with open(file_dir, "r+b") as file:
        file.seek(start_byte)
        file.write(chunk_bytes.read())

    return "Ok"


@app.route("/api/element_averages")
def list_element_averages():
    composition: list[dict[str, str | float]] = get_element_averages(TEMP_ELEMENTAL_CUBE)
    try:
        return json.dumps(composition)
    except Exception as e:
        LOG.error(f"Failed to serialize element averages: {str(e)}")
        return "Error occurred while listing element averages", 500


@app.route("/api/element_names")
def list_element_names():
    names: list[str] = get_short_element_names(TEMP_ELEMENTAL_CUBE)
    try:
        return json.dumps(names)
    except Exception as e:
        LOG.error(f"Failed to serialize element names: {str(e)}")
        return "Error occurred while listing element names", 500


@app.route("/api/get_dr_embedding")
def get_dr_embedding():
    # check if element number is provided
    if "element" not in request.args:
        LOG.error("Missing element number")
        abort(400)
    elif "threshold" not in request.args:
        LOG.error("Missing threshold value")
        abort(400)

    # Get element and threshold
    element: int = int(request.args["element"])
    threshold: int = int(request.args["threshold"])

    # Try to generate the embedding
    if not generate_embedding(element, threshold, request.args):
        abort(400)

    return "Generated embedding successfully"


@app.route("/api/get_dr_overlay")
def get_dr_overlay():
    # Check whether the overlay type is provided
    if "type" not in request.args:
        LOG.error("Missing overlay type")
        abort(400)

    overlay_type: str = request.args["type"]

    # Try to get the embedding image
    image_path: str = create_embedding_image(overlay_type)
    if not image_path:
        LOG.error("Failed to create DR embedding image")
        abort(400)

    return send_file(abspath(image_path), mimetype='image/png')

    
@app.route('/api/get_average_data', methods=['GET'])
def get_average_data():
    """Computes the average of the raw data for each bin of channels in range [low, high] on the whole painting

    :return: json list of tuples containing the bin number and the average intensity for this bin
    """
    low = int(request.args.get('low'))
    high = int(request.args.get('high'))
    bin_size = int(request.args.get('binSize'))

    datacube = get_raw_data('196_1989_M6_data 1069_1187.raw', '196_1989_M6_data 1069_1187.rpl')

    if datacube.size == 0:
        return "Error occurred while loading data", 404

    average_values = get_average_global(datacube, low, high, bin_size)
    response = json.dumps(average_values)

    return response

@app.route('/api/get_elements', methods=['GET'])
def get_elements():
    """Collect the name of the elements present in the painting
    
    :return: json list containing the names of the elements
    """
    filename = '196_1989_M6_elemental_datacube_1069_1187_rotated_inverted.dms'
    
    info = parse_rpl('196_1989_M6_data 1069_1187.rpl')
    width = int(info["width"])
    height = int(info["height"])
    c = 26

    # reading names from file
    names = []
    with open(filename, 'r') as file:
        file.seek(49 + width * height * c * 4)
        for i in range(c):
            names.append(file.readline().rstrip().replace(" ", ""))
    
    response = json.dumps(names)
    return response

@app.route('/api/get_element_spectrum', methods=['GET'])
def get_element_sectra():
    """Computes the theoretical spectrum in channel range [low, high] for an element with a bin size, as well as the element's peaks energies and intensity

    :return: json list of tuples containing the bin number and the theoretical intensity for this bin, the peak energies and the peak intensities
    """
    element = request.args.get('element')
    excitation_energy_keV = int(request.args.get('excitation'))
    low = int(request.args.get('low'))
    high = int(request.args.get('high'))
    bin_size = int(request.args.get('binSize'))
    
    response = get_theoretical_data(element, excitation_energy_keV, low, high, bin_size)
    response = json.dumps(response)
        
    return response

@app.route('/api/get_selection_spectrum', methods=['GET'])
def get_selection_sectra():
    """Gets the average spectrum of the selected pixels

    :return: json list of tuples containing the channel number and the average intensity of this channel
    """
    #selection to be retrieived from seletion tool 
    pixels = []
    low = int(request.args.get('low'))
    high = int(request.args.get('high'))
    bin_size = int(request.args.get('binSize'))

    datacube = get_raw_data('196_1989_M6_data 1069_1187.raw', '196_1989_M6_data 1069_1187.rpl')

    result = get_average_selection(datacube, pixels, low, high, bin_size)

    response = json.dumps(result)
    print("send response")
    return response

@app.route("/api/get_color_cluster", methods=["GET"])
def get_color_clusters():
    """Gets the colors and bitmask corresponding to the image-wide color clusters.

    :return json containing the ordered list of colors
    """
    # TODO: this should be whatever name we give the RGB image
    path_to_image: str = join(BACKEND_CONFIG["uploads-folder"], "rgb.tiff")
    image = get_image(path_to_image)

    # get default dim reduction config
    k_means_parameters: dict[str, str] = BACKEND_CONFIG["color-segmentation"]["k-means-parameters"]
    width: int = k_means_parameters["image-width"]
    height: int = k_means_parameters["image-height"]
    nr_attemps: int = int(k_means_parameters["nr_attemps"])
    k: int = int(k_means_parameters["k"])
    path_to_save: str = BACKEND_CONFIG["color-segmentation"]["folder"]

    labels, colors, bitmasks = get_clusters_using_k_means(image, width, height, nr_attemps, k)

    # Merge similar clusters
    colors, bitmasks = merge_similar_colors(colors, bitmasks)
    # Combine bitmasks into one
    combined_bitmask = combine_bitmasks(bitmasks)
    full_path: str = join(path_to_save, "imageClusters.png")
    image_saved: bool = save_bitmask_as_png(combined_bitmask, full_path)

    if (not image_saved):
        return "Error occurred while saving bitmask as png", 404

    response = json.dumps(colors)

    return (response, send_file(abspath(full_path), mimetype="image/png"))

@app.route("/api/get_element_color_cluster", methods=["GET"])
def get_element_color_cluster_bitmask():
    """Gets the colors and bitmasks corresponding to the color clusters of each element.

    :return json containing the combined bitmasks of the color clusters for each element.
    """
    # TODO: this should be whatever name we give the RGB image
    path_to_image: str = join(BACKEND_CONFIG["uploads-folder"], "rgb.tiff")
    image: ndarray = get_image(path_to_image)

    # get default dim reduction config
    k_means_parameters: dict[str, str] = BACKEND_CONFIG["color-segmentation"]["elemental-k-means-parameters"]
    elem_threshold: float = float(k_means_parameters["elem_threshold"])
    nr_attemps: int = int(k_means_parameters["nr_attemps"])
    k: int = int(k_means_parameters["k"])
    path_to_save: str = BACKEND_CONFIG["color-segmentation"]["folder"]

    clusters_per_elem, bitmasks_per_elem = get_elemental_clusters_using_k_means(
                                                             image, TEMP_ELEMENTAL_CUBE, CONFIG_PATH,
                                                             elem_threshold, -1, nr_attemps, k)

    number_elem: int = len(clusters_per_elem)
    img_paths = {}
    color_data = {}
    for i in range(number_elem):
        # Merge similar clusters
        clusters_per_elem[i], bitmasks_per_elem[i] = merge_similar_colors(clusters_per_elem[i], bitmasks_per_elem[i])

        # Stored combined bitmask and colors
        combined_bitmask = combine_bitmasks(bitmasks_per_elem[i])
        color_data[i] = clusters_per_elem[i]

        full_path: str = join(path_to_save, f"elementCluster_{i}.png")
        img_paths[i] = full_path
        image_saved: bool = save_bitmask_as_png(combined_bitmask, full_path)
        if (not image_saved):
            return f"Error occurred while saving bitmask for element {i} as png", 404

    response = json.dumps(color_data)

    return (response, [send_file(abspath(img_paths[i]), mimetype="image/png") for i in range(number_elem)])
