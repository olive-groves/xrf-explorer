import logging

from flask import request, redirect
from werkzeug.datastructures.file_storage import FileStorage

from xrf_explorer import app
from xrf_explorer.server.file_system.file_upload import upload_file_to_server
from xrf_explorer.server.dim_reduction.main import get_embedding, get_embedding_image


LOG: logging.Logger = logging.getLogger(__name__)


@app.route('/api')
def api():
    return "this is where the API is hosted"


@app.route('/api/info')
def info():
    return "adding more routes is quite trivial"


@app.route('/api/get_embedding')
def get_dr_embedding():
    # verify arguments
    if 'element' not in request.args:
        return "Missing element number", 400
    
    return get_embedding(request.args)


@app.route('/api/get_overlay')
def get_dr_overlay():
    if 'type' not in request.args:
        return "Missing overlay type", 400
    
    return get_embedding_image(request.args)


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
