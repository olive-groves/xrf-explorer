import logging

from os.path import exists, join, splitext
from os import makedirs

from pathlib import Path

from werkzeug.datastructures.file_storage import FileStorage

LOG: logging.Logger = logging.getLogger(__name__)


# TODO change method descriptin
def upload_file_to_server(
    file: FileStorage, upload_dir: str, file_name: str, upload_buffer_size: int = 16384
) -> bool:
    """Upload a local client file to a remote server as specified in the project's configuration.

    :param file: the file as obtained from the POST request. Can be obtained from ``flask.request.files[<name>]``
    :param config_path: path to the backend config file
    :return: True if the local file was successfully uploaded to the server AND the temporary file removed
    """

    # Create directory if it does not exist.
    if not exists(upload_dir):
        makedirs(upload_dir)

    path_to_file: str = join(Path(upload_dir, file_name))

    file.save(path_to_file, upload_buffer_size)

    # verify
    if exists(path_to_file):
        LOG.info("Uploaded {%s} to {%s}", file_name, path_to_file)
        return True

    return False


# TODO add documentation
def get_file_type(file: FileStorage):
    file_name: str | None = file.filename

    if file_name:
        return splitext(file_name)[1]
    else:
        return None
