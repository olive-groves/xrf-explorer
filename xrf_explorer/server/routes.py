import logging
import json

from flask import request, redirect
from werkzeug.datastructures.file_storage import FileStorage

from xrf_explorer import app
from xrf_explorer.server.file_system.file_upload import upload_file_to_server
from xrf_explorer.server.file_system.data_listing import get_data_sources_names
from xrf_explorer.server.file_system.element_data import get_element_names, get_element_averages


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

@app.route('/api/element_average')
def list_element_averages():
    composition: list[dict[str,  str | float]] = get_element_averages()
    print(f"Element averages: {json.dumps(composition)}")
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