import logging

from os.path import basename, exists, join
from pathlib import Path

from werkzeug.datastructures.file_storage import FileStorage
from werkzeug.utils import secure_filename

from xrf_explorer.server.file_system.config_handler import load_yml

LOG: logging.Logger = logging.getLogger(__name__)


def upload_file_to_server(file: FileStorage, config_path: str = "config/backend.yml") -> bool:
    """Upload a local client file to a remote server as specified in the project's configuration.

    :param file: the file as obtained from the POST request. Can be obtained from ``flask.request.files[<name>]``
    :param config_path: path to the backend config file
    :return: True if the local file was successfully uploaded to the server AND the temporary file removed
    """

    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        return False

    # store file on the server
    file_name: str = secure_filename(basename(file.filename))
    if file_name == '':
        LOG.error("Could not parse provided file name: {%s}", file.filename)
        return False
    path_to_file: str = join(Path(backend_config['uploads-folder']), file_name)     # store under session key folder?
    file.save(path_to_file, backend_config['upload-buffer-size'])

    # verify
    if exists(path_to_file):
        LOG.info("Uploaded {%s} to {%s}", file_name, path_to_file)
        return True

    return False
