from os import listdir
from os.path import isfile, join
from pathlib import Path

from .config_handler import load_yml


def get_files(config_path: str = "config/backend.yml") -> list[str]:
    """Return a list of all files stored in the data folder on the remote server as 
    specified in the project's configuration.

    :param config_path: path to the backend config file
    :return: list of all files stored in the folder on the server
    """

    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        return [""]

    # Path to folder where files are stored
    path = Path(backend_config['uploads-folder'])

    # Return list of all file names in the folder
    files = [f for f in listdir(path) if isfile(join(path, f))]

    # Remove unwanted files
    if ".gitignore" in files:
        files.remove(".gitignore")

    return files