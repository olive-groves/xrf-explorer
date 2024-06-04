import logging
from os.path import abspath

import yaml

LOG: logging.Logger = logging.getLogger(__name__)

APP_CONFIG: dict = None


def set_config(path: str) -> bool:
    global APP_CONFIG

    # use absolute path for extra explicitness
    path = abspath(path)

    LOG.info("Reading configuration from %s", path)
    try:
        with open(path, 'r') as config_file:
            APP_CONFIG = yaml.safe_load(config_file)
            return True
    except (FileNotFoundError, yaml.YAMLError):
        LOG.exception("Failed to access config at %s", path)
        return False


def get_config() -> dict:
    if APP_CONFIG is None:
        set_config("config/backend.yml")
    
    return APP_CONFIG
