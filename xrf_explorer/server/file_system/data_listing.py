import logging

from os import listdir
import os.path
from os.path import isdir, isfile, join
from pathlib import Path

from .config_handler import load_yml

LOG: logging.Logger = logging.getLogger(__name__)


def get_data_sources_names(config_path: str = "config/backend.yml") -> list[str]:
    """Return a list of all available data sources stored in the data folder on 
    the remote server as specified in the project's configuration.

    :param config_path: path to the backend config file
    :return: list of all data source names stored in the folder on the server
    """

    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return []

    # Path to folder where files are stored
    path = Path(backend_config['uploads-folder'])

    # Return list of all data source names in the folder
    # The data source names are the names of the folders in the data folder that contain a workspace.json
    folders: list[str] = [filename for filename in listdir(path) if isdir(join(path, filename)) and isfile(join(path, filename, "workspace.json"))]

    LOG.info(f"Successful. Data sources in folder: {folders}")
    return folders
