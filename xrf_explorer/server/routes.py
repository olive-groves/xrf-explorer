import logging
import json

from flask import request, jsonify
from werkzeug.utils import secure_filename
from werkzeug.datastructures.file_storage import FileStorage
from os.path import exists
from os import mkdir
from shutil import rmtree

from xrf_explorer import app
from xrf_explorer.server.file_system.config_handler import load_yml
from xrf_explorer.server.file_system.data_listing import get_data_sources_names


LOG: logging.Logger = logging.getLogger(__name__)
BACKEND_CONFIG: dict = load_yml("config/backend.yml")


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

    data_source_dir = f"{BACKEND_CONFIG["uploads-folder"]}/{data_source_name_secure}"

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
    delete_dir = f"{BACKEND_CONFIG["uploads-folder"]}/{request.form["dir"]}"

    if exists(delete_dir):
        rmtree(delete_dir)
        LOG.info(f"Data source at {delete_dir} removed.")
        return "Deleted", 200
    else:
        return "Directory not found", 404


@app.route("/api/upload_file_chunk", methods=["POST"])
def upload_file_chunk():
    file_dir = f"{BACKEND_CONFIG['uploads-folder']}/{request.form["dir"]}"
    start_byte = int(request.form["startByte"])
    chunk_bytes = request.files["chunkBytes"]

    # If the file does not exist, create it
    if not exists(file_dir):
        open(file_dir, "w+b").close()

    with open(file_dir, "r+b") as file:
        file.seek(start_byte)
        file.write(chunk_bytes.read())

    return "Ok"
