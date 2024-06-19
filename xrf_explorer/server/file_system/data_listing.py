import logging

from os import listdir
from os.path import isdir, isfile, join

from .helper import get_config

LOG: logging.Logger = logging.getLogger(__name__)


def get_data_sources_names() -> list[str]:
    """Return a list of all available data sources stored in the data folder on 
    the remote server as specified in the project's configuration.

    :return: list of all data source names stored in the folder on the server
    """

    # load backend config
    backend_config: dict = get_config()
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return []

    # Path to folder where files are stored
    path: str = backend_config['uploads-folder']

    # Return list of all data source names in the folder
    # The data source names are the names of the folders in the data folder that contain a workspace.json
    folders: list[str] = [filename for filename in listdir(path) if isdir(join(path, filename)) 
                          and isfile(join(path, filename, "workspace.json"))]

    LOG.info(f"Successful. Data sources in folder: {folders}")
    return folders


def get_data_source_files(data_source: str) -> list[str]:
    """Return a list of all the files stored in the folder belonging to a data source.
    Does not look at files in subdirectories.

    :param data_source: name of the data source
    :return: list of all files stored in the folder belonging to a data source
    """

    # load config
    config: dict | None = get_config()
    if not config:
        LOG.error("Config is empty")
        return []

    # Path to folder where the files are stored
    path: str = join(config['uploads-folder'], data_source)

    # Return list of all data source names in the folder
    # The data source names are the names of the folders in the data folder that contain a workspace.json
    files: list[str] = [filename for filename in listdir(path) if isfile(join(path, filename))]

    LOG.info(f"Files for data source {data_source}: {files}")
    return files
