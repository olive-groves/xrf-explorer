import logging

from os import remove, environ
from os.path import abspath, exists, join
from pathlib import Path
from socket import error

import yaml

from paramiko import AutoAddPolicy, SFTPClient, SSHClient, ssh_exception
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


def upload_file_to_server(file) -> bool:
    """Upload a local client file to a remote server as specified in the project's configuration.

    :param file: The file as obtained from the POST request. Can be obtained from ``flask.request.files[<name>]``
    :return: True if the local file was successfully uploaded to the server AND the temporary file removed
    """

    # load backend config
    config_path: str = "config/backend.yml"
    with open(config_path, 'r') as config_file:
        try:
            backend_config: dict = yaml.safe_load(config_file)
        except yaml.YAMLError:
            LOG.exception("Failed to access backend config at {config/backend.yml}")
            return False

    # store file locally (maybe can be skipped?)
    file_name: str = secure_filename(file.filename)
    if file_name == '':
        LOG.error("Could not parse provided file name")
        return False
    path_to_file: str = abspath(join(Path(backend_config['backend']['temp-folder']), file_name))
    file.save(path_to_file)

    # transfer file to server
    storage_server: dict = backend_config["storage-server"]
    file_transfer_complete: bool = False
    try:
        ssh_connection: SSHClient = SSHClient()
        ssh_connection.set_missing_host_key_policy(AutoAddPolicy)

        # establish ssh connection to server
        ssh_connection.connect(hostname=storage_server["ip"],
                               username=storage_server["user"],
                               password=environ.get('XRF_EXPLORER__CREDENTIALS__STORAGE_SERVER'),
                               port=22)

        # establish sftp connection to server
        sftp_client: SFTPClient = ssh_connection.open_sftp()
        destination: str = f"{storage_server['path']}/{file_name}"
        sftp_client.put(path_to_file, destination)
        LOG.info("Uploaded {%s} to {%s}", file.filename, destination)
        file_transfer_complete = True

        # close session
        sftp_client.close()
        ssh_connection.close()
    except (ssh_exception.AuthenticationException, ssh_exception.SSHException, error):
        LOG.exception("Failed to establish SSH connection to remote storage server")
        file_transfer_complete = False
    finally:
        local_file_removed: bool = remove_local_file(path_to_file)
        file_transfer_complete = file_transfer_complete and local_file_removed

    return file_transfer_complete
