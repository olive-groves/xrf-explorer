import logging 

from .config_handler import load_yml

LOG: logging.Logger = logging.getLogger(__name__)


def get_workspace_path(datasource, config_path: str = "config/backend.yml"):
    path = "" 

    if not path:
        LOG.error(f"Workspace {datasource} not found.")
        return ""

    LOG.info(f"Workspace {datasource} found.")
    return


def update_workspace(datasource, config_path: str = "config/backend.yml") -> bool:
    result = False 

    if not result:
        LOG.error(f"Failed to write data to workspace: {datasource}")
        return False

    LOG.info(f"Data written to workspace {datasource} successfully")
    return True
