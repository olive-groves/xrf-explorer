import logging
import json

from flask import request, jsonify, abort, send_file
from werkzeug.utils import secure_filename
from os.path import exists, join, abspath
from os import mkdir
from shutil import rmtree

from xrf_explorer import app
from xrf_explorer.server.file_system.config_handler import load_yml
from xrf_explorer.server.file_system.data_listing import get_data_sources_names
from xrf_explorer.server.file_system import get_short_element_names, get_element_averages
from xrf_explorer.server.file_system.elemental_cube import get_data_cube_path
from xrf_explorer.server.dim_reduction.embedding import generate_embedding
from xrf_explorer.server.dim_reduction.overlay import create_embedding_image
from xrf_explorer.server.spectra import *

LOG: logging.Logger = logging.getLogger(__name__)
BACKEND_CONFIG: dict = load_yml("config/backend.yml")

#TEMP_ELEMENTAL_CUBE: str = '196_1989_M6_elemental_datacube_1069_1187_rotated_inverted.dms'


@app.route("/api")
def api():
    return "this is where the API is hosted"


@app.route("/api/info")
def info():
    return "adding more routes is quite trivial"


@app.route("/api/available_data_sources")
def list_accessible_data_sources():
    """Return a list of all available data sources stored in the data folder on the remote server as specified in the project's configuration.

    :return: json list of strings representing the data sources names
    """
    try:
        return json.dumps(get_data_sources_names())
    except Exception as e:
        LOG.error(f"Failed to serialize files: {str(e)}")
        return "Error occurred while listing data sources", 500


@app.route("/api/create_ds_dir", methods=["POST"])
def create_data_source_dir():
    """Create a directory for a new data source.
    
    :request form attributes:  name - the data source name 

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
    
    :request form attributes: dir - the directory name
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
        dir - the directory name \n 
        startByte - the start byte from which bytes are uploaded \n 
        chunkBytes - the chunk  of bytes to upload
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


@app.route("/api/element_averages")
def list_element_averages():
    """List the average amount per element accross the whole painting.

    :return: json list of pairs with the element name and corresponding average value
    """
    
    datasource_name = request.args.get('datasource')
    data_cube_path = get_data_cube_path(datasource_name)
    
    composition: list[dict[str, str | float]] = get_element_averages(data_cube_path)
    try:
        return json.dumps(composition)
    except Exception as e:
        LOG.error(f"Failed to serialize element averages: {str(e)}")
        return "Error occurred while listing element averages", 500


@app.route("/api/element_names")
def list_element_names():
    """List the name of elements present in the painting.
    
    :return: json list of elements
    """
    
    datasource_name = request.args.get('datasource')
    data_cube_path = get_data_cube_path(datasource_name)

    names: list[str] = get_short_element_names(data_cube_path)
    try:
        return json.dumps(names)
    except Exception as e:
        LOG.error(f"Failed to serialize element names: {str(e)}")
        return "Error occurred while listing element names", 500


@app.route("/api/get_dr_embedding")
def get_dr_embedding():
    """Generate the dimensionality reduction embedding of an element, given a threshold.
    
    :request args: 
        element - element name \n 
        threshold - element threshold from which a pixel is selected
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
    
    :request form attributes: type - the overlay type
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

    
@app.route('/api/get_average_data', methods=['GET'])
def get_average_data():
    """Computes the average of the raw data for each bin of channels in range [low, high] on the whole painting.

    :request args: 
        low - the spectrum lower boundary \n 
        high - the spectrum higher boundary \n 
        binSize - the size of each bin
    :return: json list of tuples containing the bin number and the average intensity for this bin
    """
    low = int(request.args.get('low'))
    high = int(request.args.get('high'))
    bin_size = int(request.args.get('binSize'))
    data_source = request.args.get('datasource')
    
    datacube = get_raw_data(data_source)

    if datacube.size == 0:
        return "Error occurred while loading data", 404

    average_values = get_average_global(datacube, low, high, bin_size)
    response = json.dumps(average_values)
    
    return response

@app.route('/api/get_element_spectrum', methods=['GET'])
def get_element_sectra():
    """Compute the theoretical spectrum in channel range [low, high] for an element with a bin size, as well as the element's peaks energies and intensity.

    :request args: 
        low - the spectrum lower boundary \n 
        high - the spectrum higher boundary \n 
        binSize - the size of each bin \n 
        element - element to be plotted \n 
        excitation - excitation energy
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
    """Get the average spectrum of the selected pixels.

    :request args: 
        low - the spectrum lower boundary \n
        high - the spectrum higher boundary \n
        binSize - the size of each bin \n
        pixels - the array of corrdinates of selected pixels in the raw data coordinate system
    :return: json list of tuples containing the channel number and the average intensity of this channel
    """
    #selection to be retrieived from seletion tool 
    pixels = []
    low = int(request.args.get('low'))
    high = int(request.args.get('high'))
    bin_size = int(request.args.get('binSize'))
    data_source = request.args.get('datasource')
    
    datacube = get_raw_data(data_source)
    
    result = get_average_selection(datacube, pixels, low, high, bin_size)
    
    response = json.dumps(result)
    print("send response")
    return response
