from logging import Logger, getLogger

from os import makedirs
from os.path import join, isdir

from xrf_explorer.server.file_system import get_config

LOG: Logger = getLogger(__name__)


def get_path_to_generated_folder(data_source: str) -> str:
    """Gets the path to the generated folder for a given data source. If it does not exist, it will be created.
    
    :param data_source: The data source for which the path is requested.
    :return: The path to the generated folder for the given data source. Empty string is returned in case of error.
    """

    # load backend config
    backend_config: dict = get_config()
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return ""
    
    # Get the path to the data source folder
    path_to_data_source: str = join(backend_config['uploads-folder'], data_source)
    if not isdir(path_to_data_source):
        LOG.error(f"Data source {data_source} not found.")
        return ""
    
    # Path to the generated folder
    path_to_generated_folder: str = join(path_to_data_source, backend_config['generated-folder-name'])
    
    # Check whether it exists, if not create it
    if not isdir(path_to_generated_folder):
        makedirs(path_to_generated_folder)
        LOG.info(f"Created directory {path_to_generated_folder}.")

    return path_to_generated_folder
