import logging
import json
import json

from flask import request, redirect
from werkzeug.datastructures.file_storage import FileStorage

from xrf_explorer import app
from xrf_explorer.server.file_system.file_upload import upload_file_to_server
from xrf_explorer.server.file_system.data_listing import get_data_sources_names
from xrf_explorer.server.file_system.element_data import get_element_names, get_element_averages
from xrf_explorer.server.file_system.data_listing import get_data_sources_names
from xrf_explorer.server.file_system.element_data import get_element_names, get_element_averages

from xrf_explorer.server.spectra import *
import json

LOG: logging.Logger = logging.getLogger(__name__)


@app.route('/api')
def api():
    return "this is where the API is hosted"


@app.route('/api/info')
def info():
    return "adding more routes is quite trivial"


@app.route('/api/available_data_sources')
def list_accessible_data_sources():
    try:
        return json.dumps(get_data_sources_names())
    except Exception as e:
        LOG.error(f"Failed to serialize files: {str(e)}")
        return "Error occurred while listing data sources", 500


@app.route('/api/available_data_sources')
def list_accessible_data_sources():
    try:
        return json.dumps(get_data_sources_names())
    except Exception as e:
        LOG.error(f"Failed to serialize files: {str(e)}")
        return "Error occurred while listing data sources", 500


@app.route('/api/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':

        if 'fileUpload' not in request.files:
            LOG.error("Failed to retrieve upload file")
            return "No file part"

        file: FileStorage = request.files['fileUpload']
        if file.filename == '':     # user did not upload a file
            return "No file selected"

        if file:
            if not upload_file_to_server(file):
                LOG.error("Failed to upload file")
            return redirect("/")

    return "File upload page"


@app.route('/api/element_averages')
def list_element_averages():
    composition: list[dict[str,  str | float]] = get_element_averages()
    try:
        return json.dumps(composition)
    except Exception as e:
        LOG.error(f"Failed to serialize element averages: {str(e)}")
        return "Error occurred while listing element averages", 500


@app.route('/api/element_names')
def list_element_names():
    names: list[str] = get_element_names()
    try:
        return json.dumps(names)
    except Exception as e:
        LOG.error(f"Failed to serialize element names: {str(e)}")
        return "Error occurred while listing element names", 500


@app.route('/api/element_averages')
def list_element_averages():
    composition: list[dict[str,  str | float]] = get_element_averages()
    try:
        return json.dumps(composition)
    except Exception as e:
        LOG.error(f"Failed to serialize element averages: {str(e)}")
        return "Error occurred while listing element averages", 500


@app.route('/api/element_names')
def list_element_names():
    names: list[str] = get_element_names()
    try:
        return json.dumps(names)
    except Exception as e:
        LOG.error(f"Failed to serialize element names: {str(e)}")
        return "Error occurred while listing element names", 500
    
@app.route('/api/get_average_data', methods=['GET'])
def get_average_data():
    """Computes the average of the raw data for each bin of channels in range [low, high] on the whole painting

    :return: json list of tuples containing the bin number and the average intensity for this bin
    """
    low = int(request.args.get('low'))
    high = int(request.args.get('high'))
    bin_size = int(request.args.get('binSize'))
    
    datacube = get_raw_data('196_1989_M6_data 1069_1187.raw', '196_1989_M6_data 1069_1187.rpl')
    average_values = get_average_global(datacube, low, high, bin_size)
    response = json.dumps(average_values)
    
    return response

@app.route('/api/get_elements', methods=['GET'])
def get_elements():
    """Collect the name of the elements present in the painting
    
    :return: json list containing the names of the elements
    """
    #temporary file name
    #TODO change to actual location and dimensions of the file
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
    pixels = request.args.getlist("pixels")
    low = int(request.args.get('low'))
    high = int(request.args.get('high'))
    bin_size = int(request.args.get('binSize'))
    
    datacube = get_raw_data('196_1989_M6_data 1069_1187.raw', 'C:/Users/20210792/Downloads/info.rpl')
    
    result = get_average_selection(datacube, pixels, low, high, bin_size)
    
    response = json.dumps(result)
    print("send response")
    return response
