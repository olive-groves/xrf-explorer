from logging import Logger, getLogger
from os.path import abspath
from yaml import safe_load, YAMLError

LOG: Logger = getLogger(__name__)
APP_CONFIG: dict | None = None


def set_config(path: str) -> bool:
    """Sets the global configuration for the backend.
    :param path: The path to the configuration file.
    :return: True if the configuration file was successfully loaded.
    """

    global APP_CONFIG

    # use absolute path for extra explicitness
    abs_path: str = abspath(path)

    LOG.info("Reading configuration from %s", abs_path)
    try:
        with open(abs_path, 'r') as config_file:
            APP_CONFIG = safe_load(config_file)
            return True
    except (FileNotFoundError, YAMLError):
        LOG.exception("Failed to access config at %s", abs_path)
        APP_CONFIG = None
        return False


def get_config() -> dict | None:
    """Gets the set configuration for the backend.
    :return: A dictionary containing the configuration for the backend.
    """

    return APP_CONFIG
