import logging
import json

from flask import request, redirect
from werkzeug.datastructures.file_storage import FileStorage

from xrf_explorer import app
from xrf_explorer.server.file_system.file_upload import upload_file_to_server
from xrf_explorer.server.file_system.get_files import get_files


LOG: logging.Logger = logging.getLogger(__name__)


@app.route('/api')
def api():
    return "this is where the API is hosted"


@app.route('/api/info')
def info():
    return "adding more routes is quite trivial"


@app.route('/api/files')
def list_accessible_files():
    try:
        return json.dumps(get_files())
    except Exception as e:
        LOG.error(f"Failed to serialize files: {str(e)}")
        return "Error occurred while listing files", 500


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
