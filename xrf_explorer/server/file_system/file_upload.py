import logging

from os import remove
from os.path import basename, exists, join
from pathlib import Path

import yaml

from werkzeug.datastructures.file_storage import FileStorage
from werkzeug.utils import secure_filename

LOG: logging.Logger = logging.getLogger(__name__)


def remove_local_file(path: str) -> bool:
    """Delete a file on the local machine

    :param path: path to the file to be removed
    :return: True if successfully removed the file
    """
    # remove from temp folder
    if exists(path):
        remove(path)
        return True

    LOG.error("Could not find temporary file {%s} for removal", path)
    return False


def upload_file_to_server(file: FileStorage, config_path: str = "config/backend.yml") -> bool:
    """Upload a local client file to a remote server as specified in the project's configuration.

    :param file: the file as obtained from the POST request. Can be obtained from ``flask.request.files[<name>]``
    :param config_path: path to the backend config file
    :return: True if the local file was successfully uploaded to the server AND the temporary file removed
    """

    # load backend config
    with open(config_path, 'r') as config_file:
        try:
            backend_config: dict = yaml.safe_load(config_file)
        except yaml.YAMLError:
            LOG.exception("Failed to access backend config at {%s}", config_path)
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
