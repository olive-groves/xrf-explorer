import logging

from flask import request, redirect
from werkzeug.datastructures.file_storage import FileStorage
from os.path import exists

from xrf_explorer import app
from xrf_explorer.server.file_system.config_handler import load_yml
from xrf_explorer.server.file_system.file_upload import (
    upload_file_to_server,
    get_file_type,
)


LOG: logging.Logger = logging.getLogger(__name__)
BACKEND_CONFIG: dict = load_yml("config/backend.yml")


@app.route("/api")
def api():
    return "this is where the API is hosted"


@app.route("/api/info")
def info():
    return "adding more routes is quite trivial"


@app.route("/api/upload-data-source", methods=["POST"])
def upload_data_source():
    # TODO Add error codes
    # TODO Secure data_source_name also
    # TODO rename file_mapping and file_obj vars
    # TODO Create a workspace.yml file
    # TODO Disallow symbols like '/' in the data source name
    if "name" not in request.form:
        LOG.error("Failed to retrieve data source name")
        return "No data source name provided."

    if ("cube" not in request.files) and (
        "raw" not in request.files and "rpl" not in request.files
    ):
        LOG.error("Failed to retrieve either raw, or processed data.")
        return "Neither raw or processed data provided."

    data_source_name = request.form["name"].strip()

    if data_source_name == "":
        LOG.error("Data source name is empty.")
        return "Data source name provided, but empty."

    data_source_dir = f"{BACKEND_CONFIG["uploads_folder"]}/{data_source_name}"

    if exists(data_source_dir):
        return "Data source with that name already exists."

    file_mappings = [
        {
            "formDataName": "rgb",
            "allowedTypes": [".tiff", ".tif", ".jpg", ".bmp", ".png"],
            "uploadFileName": "rgb_image",
        },
        {
            "formDataName": "uv",
            "allowedTypes": [".tiff", ".tif", ".jpg", ".bmp", ".png"],
            "uploadFileName": "uv_image",
        },
        {
            "formDataName": "xray",
            "allowedTypes": [".tiff", ".tif", ".jpg", ".bmp", ".png"],
            "uploadFileName": "xray_image",
        },
        {"formDataName": "raw", "allowedTypes": [".raw"], "uploadFileName": "raw_data"},
        {"formDataName": "rpl", "allowedTypes": [".rpl"], "uploadFileName": "rpl_data"},
        {
            "formDataName": "cube",
            "allowedTypes": [".csv", ".dms"],
            "uploadFileName": "cube_data",
        },
    ]

    for file_obj in file_mappings:
        form_data_name = file_obj["formDataName"]
        upload_file_name = file_obj["uploadFileName"]
        allowed_types = file_obj["allowedTypes"]

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
            # TODO what happens?
            error_msg = f"File upload failed for {upload_file_full_name}."
            LOG.error(error_msg)
            return error_msg

    return "ok"
