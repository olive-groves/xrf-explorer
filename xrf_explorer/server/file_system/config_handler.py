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
        LOG.exception("Failed to read config from %s", path)
        APP_CONFIG = None
        return False


def get_config() -> dict:
    return APP_CONFIG
