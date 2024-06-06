# module responsible for giving the different paths corresponding to the files of a data source

import logging
import json
from os.path import isfile, join, exists
from pathlib import Path


from xrf_explorer.server.file_system.config_handler import load_yml


LOG: logging.Logger = logging.getLogger(__name__)
BACKEND_CONFIG: dict = load_yml("config/backend.yml")


def get_elemental_cube_name(
    data_source_folder_name: str, config_path: str = "config/backend.yml"
) -> str | None:
    """Get the location of the elemental cube file of a given datasource.

    :param data_source_folder_name: Name of the data source folder.
    :param config_path: Path to the backend config file.
    :return: Path string pointing to the elemental cube location.
    """
    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return None

    workspace_dict = get_workspace_dict(data_source_folder_name, config_path)
    if workspace_dict is None:
        return None

    return workspace_dict["elementalCubes"][0]["dataLocation"]


def get_elemental_cube_path(
    data_source: str, config_path: str = "config/backend.yml"
) -> str | None:
    """Get the path to the elemental data cube of a data source.

    :param data_source: Name of the data source folder.
    :param config_path: Path to the backend config file.
    :return: Path to the elemental data cube.
    """
    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        LOG.error("Config is empty.")
        return None

    if not exists(join(backend_config["uploads-folder"], data_source)):
        LOG.error("Data source folder name does not exist.")
        return None

    filename: str | None = get_elemental_cube_name(data_source, config_path)

    if filename is None:
        LOG.error("An error occured while trying to find elemental cube name.")
        return None

    path: str = join(Path(backend_config["uploads-folder"]), data_source, filename)

    # raise error is the path does not exist
    if not isfile(path):
        raise OSError("Provided datasource does not have an elemental cube file")

    return path


def get_raw_rpl_names(
    data_source: str, config_path: str = "config/backend.yml"
) -> tuple[str, str]:
    """Get the name of the raw data file (.raw) and the .rpl file of a given datasource

    :param datasource: Name of the datasource.
    :return: Names of the raw data and rpl files.
    """
    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return ("", "")

    data_source_dir: str = join(
        Path(backend_config["uploads-folder"]), data_source, "workspace.json"
    )
    try:
        with open(data_source_dir, "r") as workspace:
            data_json: str = workspace.read()
            data = json.loads(data_json)
            raw_data_name: str = data["spectralCubes"][0]["rawLocation"]
            rpl_name: str = data["spectralCubes"][0]["rplLocation"]
    except OSError as err:
        LOG.error("Error while getting raw and rpl file locations: {%s}", err)
        return ("", "")

    return raw_data_name, rpl_name


def get_raw_rpl_paths(
    data_source: str, config_path: str = "config/backend.yml"
) -> tuple[str, str]:
    """Get the paths to the raw data file (.raw) and the .rpl file of a given datasource

    :param datasource: Name of the datasource.
    :return: Paths to the raw data and rpl files.
    """
    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return ("", "")

    raw_name, rpl_name = get_raw_rpl_names(data_source)
    # get the path to the raw data in the server
    path_to_raw: str = join(backend_config["uploads-folder"], data_source, raw_name)

    # get the path to the rpl file in the server
    path_to_rpl: str = join(backend_config["uploads-folder"], data_source, rpl_name)

    return path_to_raw, path_to_rpl


def parse_rpl(path: str) -> dict:
    """Parse the rpl file of a data source as a dictionary, containing the following info:
        - width
        - height
        - depth
        - offset
        - data length
        - data type
        - byte order
        - record by

    :param path: path to the rpl file
    :return: Dictionary containing the attributes' name and value
    """

    try:
        with open(path, "r") as in_file:
            info = in_file.read().splitlines()  # first split on linebreak
    except OSError as err:
        LOG.error("error while reading rpl file: {%s}", err)
        return {}

    map = {}
    if info:
        for line in info:
            split = line.split()  # split on whitespace
            if len(split) == 2:
                map[split[0].strip()] = split[1].strip()  # add tuple to dictionary
    else:
        LOG.error("Error while parsing rpl file: file empty")

    return map


def get_workspace_dict(
    data_source_folder_name: str, config_path: str = "config/backend.yml"
) -> dict | None:
    """
    Returns the workspace of the specified data source in dictionary format.

    :param data_source_folder_name: Name of the data source folder.
    :param config_path: Path to the backend config file.
    :return: Dictionary format of the workspace.json
    """
    backend_config: dict = load_yml(config_path)
    workspace_json_dir = join(
        backend_config["uploads-folder"], data_source_folder_name, "workspace.json"
    )
    try:
        with open(workspace_json_dir, "r") as workspace:
            workspace_json = json.loads(workspace.read())
            return workspace_json
    except Exception:
        LOG.error(
            f"Error while reading workspace json of data source with folder name {data_source_folder_name}"
        )
        return None


def get_cube_recipe_path(
    data_source_folder_name: str, config_path: str = "config/backend.yml"
) -> str | None:
    """
    Returns the path of the data cube recipe of the specified data source. If the data cube does
    not have a recipe, the function returns None.

    :param data_source_folder_name: Name of the data source folder.
    :param config_path: Path to the backend config file.
    :return: Path of the data cube recipe
    """
    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return None

    workspace_dict = get_workspace_dict(data_source_folder_name)

    if workspace_dict is None:
        return None

    recipe_name = workspace_dict["elementalCubes"][0]["recipeLocation"]

    if recipe_name == "":
        return None

    return join(
        backend_config["uploads-folder"],
        data_source_folder_name,
        recipe_name,
    )


def get_base_image_name(
    data_source_folder_name: str, config_path: str = "config/backend.yml"
) -> str | None:
    """Get the name of the rgb image of a given data source.

    :param data_source_folder_name: Name of the data source folder.
    :param config_path: Path to the backend config file.
    :return: Name of the rgb image.
    """
    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return None

    workspace_dict = get_workspace_dict(data_source_folder_name, config_path)
    if workspace_dict is None:
        return None

    return workspace_dict["baseImage"]["imageLocation"]


def get_base_image_path(
    data_source_folder_name: str, config_path: str = "config/backend.yml"
) -> str | None:
    """Get the path to rgb image of a data source.

    :param data_source_folder_name: Name of the data source folder.
    :param config_path: Path to the backend config file.
    :return: Path to the rgb image.
    """
    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return None

    filename: str | None = get_base_image_name(data_source_folder_name, config_path)

    if filename is not None:
        return join(backend_config["uploads-folder"], data_source_folder_name, filename)
