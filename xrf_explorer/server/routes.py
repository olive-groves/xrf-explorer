import logging

from flask import request, jsonify
from werkzeug.utils import secure_filename
from werkzeug.datastructures.file_storage import FileStorage
from os.path import exists
from os import mkdir

from xrf_explorer import app
from xrf_explorer.server.file_system.config_handler import load_yml
from xrf_explorer.server.file_system.file_upload import (
    upload_file_to_server,
    get_file_type,
    get_data_source_files_spec,
)


LOG: logging.Logger = logging.getLogger(__name__)
BACKEND_CONFIG: dict = load_yml("config/backend.yml")


@app.route("/api")
def api():
    return "this is where the API is hosted"


@app.route("/api/info")
def info():
    return "adding more routes is quite trivial"


@app.route("/api/create_ds_dir", methods=["POST"])
def create_data_source_dir():
    # Check the the 'name' field was provided in the request
    if "name" not in request.form:
        error_msg = "Data source name must be provided."
        LOG.error(error_msg)
        return error_msg, 400

    data_source_name = request.form["name"].strip()

    if data_source_name == "":
        error_msg = "Data source name provided, but empty."
        LOG.error(error_msg)
        return error_msg, 400

    data_source_dir = (
        f"{BACKEND_CONFIG["uploads_folder"]}/{secure_filename(data_source_name)}"
    )

    # If the directory exists, return 400
    if exists(data_source_dir):
        error_msg = "Data source name already exists."
        LOG.error(error_msg)
        return error_msg, 400

    # create data source dir
    mkdir(data_source_dir)

    LOG.info(f"Data source directory creted at {data_source_dir}")


    return "Ok", 200


@app.route("/api/upload-data-source", methods=["POST"])
def upload_data_source():
    # TODO rename file_mapping and file_obj vars
    # TODO Create a workspace.yml file
    if "name" not in request.form:
        error_msg = "Data source name must be provided."
        LOG.error(error_msg)
        return error_msg, 400

    if ("cube" not in request.files) and (
        "raw" not in request.files and "rpl" not in request.files
    ):
        error_msg = "Either raw, or processed data must be provided."
        LOG.error(error_msg)
        return error_msg, 400

    data_source_name = request.form["name"].strip()

    if data_source_name == "":
        error_msg = "Data source name provided, but empty."
        LOG.error(error_msg)
        return error_msg, 400

    data_source_dir = (
        f"{BACKEND_CONFIG["uploads_folder"]}/{secure_filename(data_source_name)}"
    )

    if exists(data_source_dir):
        error_msg = "Data source name already exists."
        LOG.error(error_msg)
        return error_msg, 400

    files_spec = get_data_source_files_spec()

    for file_spec in files_spec:
        form_data_name = file_spec["formDataName"]
        upload_file_name = file_spec["uploadFileName"]
        allowed_types = file_spec["allowedTypes"]

        if form_data_name not in request.files:
            continue

        file: FileStorage = request.files[form_data_name]

        if file.filename == "":
            error_msg = f"Empty file attached in POST from with key {form_data_name}"
            LOG.error(error_msg)
            return error_msg

        file_type: str | None = get_file_type(file)

        if file_type not in allowed_types:
            error_msg = f"File type {file_type} not allowed for file with form key {form_data_name}"
            LOG.error(error_msg)
            return error_msg

        upload_file_full_name: str = f"{upload_file_name}{file_type}"

        file_uploaded: bool = upload_file_to_server(
            file,
            data_source_dir,
            upload_file_full_name,
            BACKEND_CONFIG["upload_buffer_size"],
        )

        if not file_uploaded:
            # Delete the whole data source?
            error_msg = f"File upload failed for {upload_file_full_name}."
            LOG.error(error_msg)
            return error_msg

    return jsonify({"message": "Data source uploaded successfully"}), 200
