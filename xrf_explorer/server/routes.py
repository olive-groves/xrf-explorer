import logging
import json

from flask import abort, request, redirect, send_file
from werkzeug.datastructures.file_storage import FileStorage

from xrf_explorer import app
from xrf_explorer.server.file_system.file_upload import upload_file_to_server
from xrf_explorer.server.file_system.data_listing import get_data_sources_names
from xrf_explorer.server.dim_reduction.main import get_embedding, get_embedding_image


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


@app.route('/api/get_embedding')
def get_dr_embedding():
    # check if element number is provided
    if 'element' not in request.args:
        LOG.error("Missing element number")
        abort(400)

    # Try to generate the embedding
    if not get_embedding(request.args):
        abort(400)

    return "Generated embedding successfully"


@app.route('/api/get_overlay')
def get_dr_overlay():
    # Check whether the overlay type is provided
    if 'type' not in request.args:
        LOG.error("Missing overlay type")
        abort(400)

    # Try to get the embedding image
    image_path = get_embedding_image(request.args)
    if len(image_path) == 0:
        abort(400)

    return send_file(image_path, mimetype='image/png')
