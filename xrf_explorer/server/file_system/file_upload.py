from os import remove
from os.path import abspath, exists, join
from pathlib import Path

import yaml

from paramiko import AutoAddPolicy, SFTPClient, SSHClient
from werkzeug.utils import secure_filename


def upload_file_to_server(file, temp_folder: str) -> str:

    # store file locally (maybe can be skipped?)
    file_name: str = secure_filename(file.filename)
    # TODO: secure_filename may return empty filename
    path_to_file: str = abspath(join(Path(temp_folder), file_name))
    file.save(path_to_file)

    # load backend config
    with open('config/backend.yml', 'r') as config_file:
        try:
            backend_config: dict = yaml.safe_load(config_file)
        except yaml.YAMLError as e:
            return "Failed to upload file: \n" + e.__str__()

    # transfer file to server
    storage_server: dict = backend_config["storage-server"]
    print("sending to server...")
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
    sftp_client.put(path_to_file, f"{storage_server["path"]}/{file_name}")
    sftp_client.close()
    ssh_connection.close()
    print("sent to server :)")

    # remove from temp folder
    if exists(path_to_file):
        remove(path_to_file)
        return "Uploaded file"

    print("ayo, where'd me file go???")

    return "Whoops"
