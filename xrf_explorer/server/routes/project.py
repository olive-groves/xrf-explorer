import json

from logging import Logger, getLogger
from os import mkdir, unlink, listdir, rmdir
from os.path import abspath, join, isdir, isfile
from shutil import rmtree

from flask import request, abort, send_file, jsonify
from markupsafe import escape

from xrf_explorer import app
from xrf_explorer.server.file_system import get_config
from xrf_explorer.server.file_system.sources import get_data_sources_names, get_data_source_files
from xrf_explorer.server.file_system.workspace import update_workspace, get_path_to_workspace
from xrf_explorer.server.routes.helper import validate_config

LOG: Logger = getLogger(__name__)


@app.route("/api/data_sources")
def list_accessible_data_sources():
    """
    Return a list of all available data sources stored in the data folder on the remote server as specified in the
    project's configuration.

    :return: JSON list of strings representing the data sources names
    """
    return json.dumps(get_data_sources_names())


@app.route("/api/<data_source>/files")
def datasource_files(data_source: str):
    """
    Return a list of all available files for a data source.

    :param data_source: The name of the data source to get the files for
    :return: JSON list of strings representing the file names
    """
    return json.dumps(get_data_source_files(data_source))


@app.route("/api/<data_source>/workspace", methods=["GET", "POST"])
def get_workspace(data_source: str):
    """
    Gets the workspace content for the specified data source or writes to it if a POST request is made.

    :param data_source: The name of the data source to get the workspace content for
    :return: If a GET request is made, the workspace content is sent as a json file. If a POST request is made, a
        confirmation message is sent
    """

    if request.method == "POST":
        # Get send json file
        data: any = request.get_json()

        # Write content to the workspace
        result: bool = update_workspace(data_source, data)

        # Check if writing was successful
        if not result:
            abort(400)

        return f"Data written to workspace {escape(data_source)} successfully"
    else:
        # Read content from the workspace
        path: str = get_path_to_workspace(data_source)

        # Check if the workspace exists
        if not path:
            abort(404)

        # Send the json file
        return send_file(abspath(path), mimetype='application/json')


@app.route("/api/<data_source>/create", methods=["POST"])
def create_data_source_dir(data_source: str):
    """
    Create a directory for a new data source.

    :param data_source: The name of the data source to create
    :return: JSON with directory name
    """
    # Get config
    config: dict | None = get_config()

    error_response_config: tuple[str, int] | None = validate_config(config)
    if error_response_config:
        return error_response_config

    if data_source in get_data_sources_names():
        error_msg: str = "Data source name already exists."
        LOG.error(error_msg)
        return error_msg, 400

    data_source_dir = join(config["uploads-folder"], data_source)

    # create data source dir
    if not isdir(data_source_dir):
        LOG.info(f"Creating data source directory at {data_source_dir}")
        mkdir(data_source_dir)

    return jsonify({"dataSourceDir": data_source})


@app.route("/api/<data_source>/remove", methods=["POST"])
def remove_data_source(data_source: str):
    """
    Removes `workspace.json` from a data source,

    :param data_source: The name of the data source to be aborted
    :return: JSON with directory name
    """
    # Get config
    config: dict | None = get_config()
    LOG.info(f"Aborting data source directory creation for {data_source}")

    error_response_config: tuple[str, int] | None = validate_config(config)
    if error_response_config:
        return error_response_config

    data_source_path: str = join(config['uploads-folder'], data_source)
    workspace_path: str = join(data_source_path, "workspace.json")
    generated_path: str = join(data_source_path, "generated")

    if isdir(generated_path):
        # remove generated files
        rmtree(generated_path)

    if isfile(workspace_path):
        # remove workspace.json
        LOG.info(f"Removing workspace.json at {workspace_path}")
        unlink(workspace_path)

    if isdir(data_source_path) and len(listdir(data_source_path)) == 0:
        # remove directory if it is empty
        rmdir(data_source_path)

    return jsonify({"dataSourceDir": data_source})


@app.route("/api/<data_source>/delete", methods=["DELETE"])
def delete_data_source(data_source: str):
    """
    Completely deletes and removes all files from data source.

    :param data_source: The data source to delete.
    :return: JSON with directory name
    """
    # Get config
    config: dict | None = get_config()
    LOG.info(f"Aborting data source directory creation for {data_source}")

    data_source_dir: str = join(config['uploads-folder'], data_source)

    if not isdir(data_source_dir):
        error_msg: str = "Data source name does not exist."
        LOG.error(error_msg)
        return error_msg, 400

    # remove data source dir
    LOG.info(f"Removing data source directory at {data_source_dir}")
    rmtree(data_source_dir)

    return jsonify({"dataSourceDir": data_source})


@app.route("/api/<data_source>/upload/<file_name>/<int:start>", methods=["POST"])
def upload_chunk(data_source: str, file_name: str, start: int):
    """
    Upload a chunk of bytes to a file in specified data source.

    :param data_source: The name of the data source to upload the chunk to
    :param file_name: The name of the file to upload the chunk to
    :param start: The start index of the chunk in the specified file
    :return: A message indicating the success of the upload
    """

    # get config
    config: dict | None = get_config()

    error_response_config: tuple[str, int] | None = validate_config(config)
    if error_response_config:
        return error_response_config

    # get file location
    path: str = abspath(join(config['uploads-folder'], data_source, file_name))

    # test that path is a sub path of the uploads-folder
    if not path.startswith(abspath(join(config['uploads-folder'], data_source))):
        LOG.info("Attempted to upload chunk to %s which is not allowed", path)
        return "Unauthorized file chunk location", 401

    # create file if it does not exist
    if not isfile(path):
        LOG.info("Created file %s", path)
        open(path, "x+b").close()

    # write chunk to file
    with open(path, "r+b") as file:
        file.seek(start)
        file.write(request.get_data())
        LOG.info("Wrote chunk from %i into %s", start, path)

    return "Uploaded file chunk", 200
