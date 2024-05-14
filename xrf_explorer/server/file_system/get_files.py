import logging

from os import listdir
from os.path import isfile, join
from pathlib import Path

from .config_handler import load_yml

LOG: logging.Logger = logging.getLogger(__name__)


def get_files(config_path: str = "config/backend.yml") -> list[str]:
    """Return a list of all files stored in the data folder on the remote server as 
    specified in the project's configuration.

    :param config_path: path to the backend config file
    :return: list of all files stored in the folder on the server
    """

    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return [""]

    # Path to folder where files are stored
    path = Path(backend_config['uploads-folder'])

    # Return list of all file names in the folder
    files: list[str] = [filename for filename in listdir(path) if isfile(join(path, filename))]

    # Remove unwanted files
    if ".gitignore" in files:
        try:
            files.remove(".gitignore")
        except Exception as e:
            LOG.error(f"Failed to remove .gitignore: {str(e)}")

    LOG.info(f"Successful. Files in folder: {files}")
    return files
