import logging 

from os.path import isfile, join
from json import load, dump

from .config_handler import load_yml

LOG: logging.Logger = logging.getLogger(__name__)


def get_workspace_path(datasource: str, config_path: str = "config/backend.yml") -> str:
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

    # Check if the workspace exists
    if not isfile(path_to_workspace):
        LOG.error(f"Workspace {datasource} not found.")
        return ""

    LOG.info(f"Workspace {datasource} found.")
    return path_to_workspace


def update_workspace(datasource: str, new_workspace, config_path: str = "config/backend.yml") -> bool:
    """Update the workspace.json file for a given datasource.
    
    :param datasource: The name of the datasource
    :param args: The data to write to the workspace
    :param config_path: The path to the backend config file
    :return: True if the workspace was updated successfully, False otherwise.
    """

    # get path to workspace
    path: str = get_workspace_path(datasource, config_path)
    if not path:
        return False
    
    try:
        # write updated workspace back to file
        with open(path, "w") as json_file:
            dump(new_workspace, json_file)
        
    except OSError as e:
        LOG.error(f"Failed to write data to workspace: {str(e)}")
        return False

    LOG.info(f"Data written to workspace {datasource} successfully")
    return True
