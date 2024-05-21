import logging
import json

from flask import abort, request, redirect, send_file
from werkzeug.datastructures.file_storage import FileStorage

from xrf_explorer import app
from xrf_explorer.server.file_system.file_upload import upload_file_to_server
from xrf_explorer.server.file_system.data_listing import get_data_sources_names
from xrf_explorer.server.file_system.element_data import get_element_names, get_element_averages
from xrf_explorer.server.dim_reduction.embedding import generate_embedding
from xrf_explorer.server.dim_reduction.overlay import create_embedding_image


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


@app.route('/api/get_dr_embedding')
def get_dr_embedding():
    # check if element number is provided
    if 'element' not in request.args:
        LOG.error("Missing element number")
        abort(400)
    elif 'threshold' not in request.args:
        LOG.error("Missing threshold value")
        abort(400)

    # Get element and threshold
    element: int = int(request.args['element'])
    threshold: int = int(request.args['threshold'])

    # Try to generate the embedding
    if not generate_embedding(element, threshold, request.args):
        abort(400)

    return "Generated embedding successfully"


@app.route('/api/get_dr_overlay')
def get_dr_overlay():
    # Check whether the overlay type is provided
    if 'type' not in request.args:
        LOG.error("Missing overlay type")
        abort(400)
    
    overlay_type: str = request.args['type']

    # Try to get the embedding image
    image_path: str = create_embedding_image(overlay_type)
    if not image_path:
        LOG.error("Failed to create DR embedding image")
        abort(400)

    return send_file(image_path, mimetype='image/png')
