import logging
import json

from flask import request, jsonify, abort, send_file
from werkzeug.utils import secure_filename
from os.path import exists, join, abspath, basename
from os import mkdir
from shutil import rmtree
from markupsafe import escape
from numpy import ndarray
from typing import List

from xrf_explorer import app
from xrf_explorer.server.file_system.config_handler import load_yml
from xrf_explorer.server.file_system.workspace_handler import get_path_to_workspace, update_workspace
from xrf_explorer.server.file_system.data_listing import get_data_sources_names
from xrf_explorer.server.file_system import get_short_element_names, get_element_averages
from xrf_explorer.server.file_system.file_access import *
from xrf_explorer.server.dim_reduction.embedding import generate_embedding
from xrf_explorer.server.dim_reduction.overlay import create_embedding_image
from xrf_explorer.server.spectra import *
from xrf_explorer.server.color_seg import (
    get_image, combine_bitmasks, get_clusters_using_k_means,
    get_elemental_clusters_using_k_means, merge_similar_colors,
    save_bitmask_as_png, convert_to_hex
)
from xrf_explorer.server.file_system.from_dms import (
    get_elemental_datacube_dimensions_from_dms,
)

LOG: logging.Logger = logging.getLogger(__name__)
CONFIG_PATH: str = 'config/backend.yml'
BACKEND_CONFIG: dict = load_yml(CONFIG_PATH)

TEMP_RGB_IMAGE: str = '196_1989_RGB.tif'

colors_per_elem: ndarray
bitmasks_per_elem: ndarray


@app.route("/api")
def api():
    return "Welcome to the XRF-Explorer API"


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


@app.route("/api/create_ds_dir", methods=["POST"])
def create_data_source_dir():
    """Create a directory for a new data source.
    
    :request form attributes:  **name** - the data source name 

    :return: json with directory name
    """
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
    """Delete a data source directory.
    
    :request form attributes: **dir** - the directory name
    """
    delete_dir = join(BACKEND_CONFIG["uploads-folder"], request.form["dir"])

    if exists(delete_dir):
        rmtree(delete_dir)
        LOG.info(f"Data source at {delete_dir} removed.")
        return "Deleted", 200
    else:
        return "Directory not found", 404


@app.route("/api/upload_file_chunk", methods=["POST"])
def upload_file_chunk():
    """Upload a chunk of bytes to a file.
    
    :request form attributes: 
        **dir** - the directory name \n 
        **startByte** - the start byte from which bytes are uploaded \n 
        **chunkBytes** - the chunk  of bytes to upload
    """
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


@app.route("/api/<data_source>/element_averages")
def list_element_averages(data_source: str):
    """List the average amount per element accross the whole painting.
    
    :param data_source: data_source to get the element averages from
    :return: json list of pairs with the element name and corresponding average value
    """
    
    path: str = get_elemental_cube_path(data_source)
    
    composition: list[dict[str, str | float]] = get_element_averages(path)
    try:
        return json.dumps(composition)
    except Exception as e:
        LOG.error(f"Failed to serialize element averages: {str(e)}")
        return "Error occurred while listing element averages", 500


@app.route("/api/<data_source>/element_names")
def list_element_names(data_source: str):
    """List the name of elements present in the painting.
    
    :param data_source: data_source to get the element names from
    :return: json list of elements
    """
    path: str = get_elemental_cube_path(data_source)

    names: list[str] = get_short_element_names(path)
    try:
        return json.dumps(names)
    except Exception as e:
        LOG.error(f"Failed to serialize element names: {str(e)}")
        return "Error occurred while listing element names", 500


@app.route("/api/get_dr_embedding")
def get_dr_embedding():
    """Generate the dimensionality reduction embedding of an element, given a threshold.
    
    :request args: 
        **element** - element name \n 
        **threshold** - element threshold from which a pixel is selected
    """
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
    """Generate the dimensionality reduction overlay with a given type.
    
    :request form attributes: **type** - the overlay type
    :return: overlay image file
    """
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

    
@app.route('/api/<data_source>/get_average_data', methods=['GET'])
def get_average_data(data_source):
    """Computes the average of the raw data for each bin of channels in range [low, high] on the whole painting.

    :param data_source: data_source to get the average raw data from
    :request args: 
        **low** - the spectrum lower boundary \n 
        **high** - the spectrum higher boundary \n 
        **binSize** - the size of each bin
    :return: json list of tuples containing the bin number and the average intensity for this bin
    """
    low = int(request.args.get('low'))
    high = int(request.args.get('high'))
    bin_size = int(request.args.get('binSize'))
    datacube: np.ndarray = get_raw_data(data_source)

    if datacube.size == 0:
        return "Error occurred while loading data", 404

    average_values: list = get_average_global(datacube, low, high, bin_size)
    response = json.dumps(average_values)

    return response

@app.route('/api/get_element_spectrum', methods=['GET'])
def get_element_sectra():
    """Compute the theoretical spectrum in channel range [low, high] for an element with a bin size, as well as the element's peaks energies and intensity.

    :request args: 
        **low** - the spectrum lower boundary \n 
        **high** - the spectrum higher boundary \n 
        **binSize** - the size of each bin \n 
        **element** - element to be plotted \n 
        **excitation** - excitation energy
    :return: json list of tuples containing the bin number and the theoretical intensity for this bin, the peak energies and the peak intensities
    """
    element: str = request.args.get('element')
    excitation_energy_keV = int(request.args.get('excitation'))
    low = int(request.args.get('low'))
    high = int(request.args.get('high'))
    bin_size = int(request.args.get('binSize'))
    
    response: list = get_theoretical_data(element, excitation_energy_keV, low, high, bin_size)
    response = json.dumps(response)
        
    return response

@app.route('/api/<data_source>/get_selection_spectrum', methods=['GET'])
def get_selection_sectra(data_source):
    """Get the average spectrum of the selected pixels.

    :request args: 
        **low** - the spectrum lower boundary \n
        **high** - the spectrum higher boundary \n
        **binSize** - the size of each bin \n
        **pixels** - the array of corrdinates of selected pixels in the raw data coordinate system
    :return: json list of tuples containing the channel number and the average intensity of this channel
    """
    #selection to be retrieived from seletion tool 
    pixels: list[tuple[int, int]] = []
    low = int(request.args.get('low'))
    high = int(request.args.get('high'))
    bin_size = int(request.args.get('binSize'))
    datacube: list = get_raw_data(data_source)
    result: list = get_average_selection(datacube, pixels, low, high, bin_size)
    
    response = json.dumps(result)
    print("send response")
    return response

@app.route('/api/<data_source>/get_color_cluster', methods=['GET'])
def get_color_clusters(data_source: str):
    '''Gets the colors corresponding to the image-wide color clusters, and saves the 
    corresponding bitmasks.

    :param data_source: data_source to get the element averages from
    :return json containing the ordered list of colors
    '''
    # currently hardcoded, this should be whatever name+path we give the RGB image
    path_to_image: str = join(BACKEND_CONFIG['uploads-folder'], TEMP_RGB_IMAGE)
    image = get_image(path_to_image)
    data_cube_path: str = get_elemental_cube_path(data_source)

    # get default dim reduction config
    k_means_parameters: dict[str, str] = BACKEND_CONFIG['color-segmentation']['k-means-parameters']
    width: int
    height: int
    width, height, _, _ = get_elemental_datacube_dimensions_from_dms(data_cube_path)
    nr_attempts: int = int(k_means_parameters['nr-attempts'])
    k: int = int(k_means_parameters['k'])
    path_to_save: str = BACKEND_CONFIG['color-segmentation']['folder']

    colors: ndarray
    bitmasks: ndarray
    colors, bitmasks = get_clusters_using_k_means(image, width, height, nr_attempts, k)

    # Merge similar clusters
    colors, _ = merge_similar_colors(colors, bitmasks)
    # Combine bitmasks into one
    combined_bitmask: ndarray = combine_bitmasks(bitmasks)

    # Save bitmask
    full_path: str = join(path_to_save, data_source, 'imageClusters.png')
    image_saved: bool = save_bitmask_as_png(combined_bitmask, full_path)
    if (not image_saved):
        return 'Error occurred while saving bitmask as png', 500

    colors = convert_to_hex(colors)
    response = json.dumps(colors)

    return (response)

@app.route('/api/<data_source>/get_color_cluster_bitmask', methods=['GET'])
def get_color_cluster_bitmask(data_source: str):
    """
    Returns the png bitmask for the color clusters over the whole painting.

    :param data_source: data_source to get the element averages from
    :return bitmask png file for the whole image
    """

    # Get element and threshold
    element: int = int(request.args["element"])

    # Get path to image
    path_to_save: str = BACKEND_CONFIG['color-segmentation']['folder']
    full_path: str = join(path_to_save, data_source, f'imageClusters.png')
    if not exists(full_path):
        return f'Bitmasks for element {element} not generated', 500

    response = send_file(abspath(full_path), mimetype='image/png')
    return response

@app.route('/api/<data_source>/get_element_color_cluster', methods=['GET'])
def get_element_color_cluster(data_source: str):
    '''Gets the colors corresponding to the color clusters of each element.

    :param data_source: data_source to get the element averages from
    :return json containing the color clusters for each element.
    '''
    # currently hardcoded, this should be whatever name+path we give the RGB image
    path_to_image: str = join(BACKEND_CONFIG['uploads-folder'], TEMP_RGB_IMAGE)
    image: ndarray = get_image(path_to_image)
    data_cube_path: str = get_elemental_cube_path(data_source)

    # get default dim reduction config
    k_means_parameters: dict[str, str] = BACKEND_CONFIG['color-segmentation']['elemental-k-means-parameters']
    elem_threshold: float = float(k_means_parameters['elem-threshold'])
    nr_attempts: int = int(k_means_parameters['nr-attempts'])
    k: int = int(k_means_parameters['k'])
    path_to_save: str = BACKEND_CONFIG['color-segmentation']['folder']

    colors_per_elem: ndarray
    bitmasks_per_elem: ndarray
    colors_per_elem, bitmasks_per_elem = get_elemental_clusters_using_k_means(
                                                             image, data_cube_path, elem_threshold, -1, -1, nr_attempts, k)

    color_data: list[list[str]] = []
    for i in range(len(colors_per_elem)):
        # Merge similar clusters
        colors_per_elem[i], _ = merge_similar_colors(colors_per_elem[i], bitmasks_per_elem[i])
        color_data.append(convert_to_hex(colors_per_elem[i]))

        # Stored combined bitmask and colors
        combined_bitmask: ndarray = combine_bitmasks(bitmasks_per_elem[i])

        # Save bitmask
        full_path: str = join(path_to_save, data_source, f'elementCluster_{i}.png')
        image_saved: bool = save_bitmask_as_png(combined_bitmask, full_path)
        if (not image_saved):
            return f'Error occurred while saving bitmask for element {i} as png', 500

    response = json.dumps(color_data)

    return response

@app.route('/api/<data_source>/get_element_color_cluster_bitmask', methods=['GET'])
def get_element_color_cluster_bitmask(data_source: str):
    """
    Returns, for the requested element, the png bitmask for the color clusters.

    :param data_source: data_source to get the element averages from

    :request args:
        **element** - element index
    :return bitmask png file for the given element
    """
    # check if element number is provided
    if "element" not in request.args:
        LOG.error("Missing element number")
        abort(400)

    # Get element and threshold
    element: int = int(request.args["element"])

    # Save bitmask
    path_to_save: str = BACKEND_CONFIG['color-segmentation']['folder']
    full_path: str = join(path_to_save, data_source, f'elementCluster_{element}.png')
    if not exists(full_path):
        return f'Bitmasks for element {element} not generated', 500

    response = send_file(abspath(full_path), mimetype='image/png')
    return response
