import logging 

from os import makedirs
from os.path import join, isdir

from xrf_explorer.server.file_system import get_config, get_path_to_generated_folder

LOG: logging.Logger = logging.getLogger(__name__)


def get_path_to_cs_folder(data_source: str) -> str:
    """Get the path to the color segmentation folder for a given datasource. If it does not exist the folder is
    created.
    
    :param data_source: The name of the datasource
    :return: The path to the color segmentation folder for the given datasource.
    """

    # load backend config
    backend_config: dict = get_config()
    if not backend_config:  # config is empty
        LOG.error("Could not find path to color segmentation folder: config is empty")
        return ""

    # Get path to generated folder of the data source
    path_to_generated_folder: str = get_path_to_generated_folder(data_source)
    if not path_to_generated_folder:
        return ""

    # Path to the color segmentation folder
    path_to_cs_folder: str = join(path_to_generated_folder, backend_config['cs-folder-name'])

    # Check if the color segmentation folder exists, otherwise create it
    if not isdir(path_to_cs_folder):
        makedirs(path_to_cs_folder)
        LOG.info(f"Created directory {path_to_cs_folder}.")

    LOG.info(f"Color segmentation folder {data_source} found.")
    return path_to_cs_folder
