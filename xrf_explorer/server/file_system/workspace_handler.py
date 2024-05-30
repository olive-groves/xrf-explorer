import logging 

from os.path import isfile, isdir, join
from json import dump

from .config_handler import load_yml

LOG: logging.Logger = logging.getLogger(__name__)


def get_path_to_workspace(datasource: str, config_path: str = "config/backend.yml") -> str:
    """Get the path to the workspace.json file for a given datasource.
    
    :param datasource: The name of the datasource
    :param config_path: The path to the backend config file
    :return: The path to the workspace.json file for the given datasource. If the workspace does not exist, return an empty string.
    """

    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return ""

    # Path to the workspace.json file
    path_to_workspace: str = join(backend_config['uploads-folder'], datasource, 'workspace.json')

    # Check if the datasource exists
    if not isfile(path_to_workspace):
        LOG.error(f"Datasource {datasource} not found.")
        return ""

    LOG.info(f"Workspace {datasource} found.")
    return path_to_workspace


def update_workspace(datasource: str, new_workspace: any, config_path: str = "config/backend.yml") -> bool:
    """Update the workspace.json file for a given datasource.
    
    :param datasource: The name of the datasource
    :param new_workspace: The data to write to the workspace
    :param config_path: The path to the backend config file
    :return: True if the workspace was updated successfully, False otherwise.
    """

    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return False

    # Get the path to the data source folder
    data_source_folder: str = join(backend_config['uploads-folder'], datasource)
    if not isdir(data_source_folder):
        LOG.error(f"Datasource {datasource} not found.")
        return False
    
    # Path to the workspace.json file
    path_to_workspace: str = join(data_source_folder, 'workspace.json')
    
    # Try to update workspace
    try:
        # update the workspace present or create a new one
        with open(path_to_workspace, "w") as json_file:
            dump(new_workspace, json_file)
        
    except OSError as e:
        LOG.error(f"Failed to write data to workspace: {str(e)}")
        return False

    LOG.info(f"Data written to workspace {datasource} successfully")
    return True
