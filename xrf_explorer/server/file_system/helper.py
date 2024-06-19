from logging import Logger, getLogger
from os import makedirs
from os.path import abspath, join , isdir

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


def get_path_to_generated_folder(data_source: str) -> str | None:
    """Gets the path to the generated folder for a given data source. If it does not exists, it will be created.

    :param data_source: The data source for which the path is requested.
    :return: The path to the generated folder for the given data source.
    """

    # load backend config
    backend_config: dict = get_config()
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return None

    # Get the path to the data source folder
    path_to_data_source: str = join(backend_config['uploads-folder'], data_source)
    if not isdir(path_to_data_source):
        LOG.error(f"Data source {data_source} not found.")
        return None

    # Path to the generated folder
    path_to_generated_folder: str = join(path_to_data_source, backend_config['generated-folder-name'])

    # Check whether it exists, if not create it
    if not isdir(path_to_generated_folder):
        makedirs(path_to_generated_folder)
        LOG.info(f"Created directory {path_to_generated_folder}.")

    return path_to_generated_folder
