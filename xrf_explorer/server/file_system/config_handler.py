import logging
from os.path import abspath

import yaml

LOG: logging.Logger = logging.getLogger(__name__)

APP_CONFIG: dict | None = None


def set_config(path: str) -> bool:
    """Sets the global configuration for the backend.
    :param path: The path to the configuration file.
    :return: True if the configuration file was successfully loaded.
    """

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
        APP_CONFIG = None
        return False


def get_config() -> dict | None:
    """Gets the set configuration for the backend.
    :return: A dictionary containing the configuration for the backend.
    """

    return APP_CONFIG
