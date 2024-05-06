import logging

from os import remove
from os.path import abspath, exists, join
from pathlib import Path
from socket import error

import yaml

from paramiko import AutoAddPolicy, SFTPClient, SSHClient, ssh_exception
from werkzeug.utils import secure_filename

LOG: logging.Logger = logging.getLogger(__name__)


def remove_local_file(path: str) -> bool:
    # remove from temp folder
    if exists(path):
        remove(path)
        return True

    LOG.error("Could not find temporary file {%s} for removal", path)
    return False


def upload_file_to_server(file, temp_folder: str) -> bool:
    # store file locally (maybe can be skipped?)
    file_name: str = secure_filename(file.filename)
    if file_name == '':
        LOG.error("could not parse provided file name")
        return False
    path_to_file: str = abspath(join(Path(temp_folder), file_name))
    file.save(path_to_file)

    # load backend config
    config_path: str = "config/backend.yml"
    with open(config_path, 'r') as config_file:
        try:
            backend_config: dict = yaml.safe_load(config_file)
        except yaml.YAMLError:
            LOG.exception("Failed to access backend config at {config/backend.yml}")
            return False

    # transfer file to server
    storage_server: dict = backend_config["storage-server"]
    file_transfer_complete: bool = False
    try:
        ssh_connection: SSHClient = SSHClient()
        ssh_connection.set_missing_host_key_policy(AutoAddPolicy)

        # establish ssh connection to server
        ssh_connection.connect(hostname=storage_server["ip"],
                               username=storage_server["user"],
                               password='giveaccess',
                               port=22)
        # TODO: find somewhere to store password

        # establish sftp connection to server
        sftp_client: SFTPClient = ssh_connection.open_sftp()
        destination: str = f"{storage_server['path']}/{file_name}"
        sftp_client.put(path_to_file, destination)
        LOG.info("uploaded {%s} to {%s}", file.filename, destination)
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
