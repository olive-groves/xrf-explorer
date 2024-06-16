#  module responsible for giving the different paths corresponding to the files of a data source

import logging
import json
from os.path import isfile, join, exists, abspath
from pathlib import Path

from matplotlib.font_manager import json_dump


from xrf_explorer.server.file_system.config_handler import get_config
from xrf_explorer.server.file_system.workspace_handler import get_path_to_workspace

LOG: logging.Logger = logging.getLogger(__name__)


def get_elemental_cube_file_names(data_source: str) -> list[str] | None:
    """Get the names of the elemental cube files of a given datasource.

    :param data_source: Name of the data source folder.
    :return: Names of the elemental cube files.
    """

    workspace_dict = get_workspace_dict(data_source)
    if workspace_dict is None:
        return None

    return [cube_info["dataLocation"] for cube_info in workspace_dict["elementalCubes"]]


def get_elemental_cube_path_from_name(data_source: str, cube_name: str) -> list[str] | None:
    """Get the path to the elemental data cube of the given cube and data source.

    :param data_source: Name of the data source folder.
    :param cube_name: Name of the elemental cube.
    :return: Path to the elemental data cube with the given name.
    """

    # Load backend config
    backend_config: dict | None = get_config()
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return None
    
    # Load workspace
    workspace_dict = get_workspace_dict(data_source)
    if workspace_dict is None:
        return None
    
    # Find the file name with the given name
    for cube_info in workspace_dict['elementalCubes']:
        if cube_info['name'] == cube_name:
            return join(backend_config["uploads-folder"], data_source, cube_info['dataLocation'])
    
    return None


def get_elemental_cube_path(data_source_folder: str) -> str | None:
    """Get the path to the elemental data cube of a data source.

    :param data_source_folder: Name of the data source folder.
    :return: Path to the elemental data cube.
    """
    # load backend config
    backend_config: dict | None = get_config()
    if not backend_config:  # config is empty
        LOG.error("Config is empty.")
        return None

    if not exists(join(backend_config["uploads-folder"], data_source_folder)):
        LOG.error(f"Data source folder at {
                  join(backend_config["uploads-folder"], data_source_folder)} does not exist.")
        return None

    filename: str | None = get_elemental_cube_file_names(data_source_folder)[0]

    if filename is None:
        LOG.error("An error occurred while trying to find elemental cube name.")
        return None

    path: str = join(
        Path(backend_config["uploads-folder"]), data_source_folder, filename)

    # raise error is the path does not exist
    if not isfile(path):
        raise OSError(
            "Provided datasource does not have an elemental cube file")

    return path


def get_elemental_cube_recipe_path(data_source: str) -> str | None:
    """Get the location of the elemental cube recipe file of a given datasource

    :param data_source: Name of the datasource.
    :return: Path string pointing to the recipe of the elemental cube.
    """
    # load backend config
    backend_config: dict | None = get_config()
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return None

    data_source_dir: str = join(backend_config["uploads-folder"], data_source)
    workspace_path: str = join(data_source_dir, "workspace.json")
    try:
        with open(workspace_path, 'r') as workspace:
            data_json: str = workspace.read()
            data = json.loads(data_json)
            recipe_name: str = data["elementalCubes"][0]["recipeLocation"]
    except OSError as err:
        LOG.error("Error while getting recipe of elemental cube: {%s}", err)
        return None

    return abspath(join(data_source_dir, recipe_name))


def get_raw_rpl_names(data_source: str
                      ) -> tuple[str, str]:
    """Get the name of the raw data file (.raw) and the .rpl file of a given datasource

    :param data_source: Name of the data source.
    :return: Names of the raw data and rpl files.
    """
    # load backend config
    backend_config: dict | None = get_config()
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return "", ""

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
        return "", ""

    return raw_data_name, rpl_name


def get_raw_rpl_paths(data_source: str) -> tuple[str, str]:
    """Get the paths to the raw data file (.raw) and the .rpl file of a given datasource

    :param data_source: Name of the data source.
    :return: Paths to the raw data and rpl files.
    """
    # load backend config
    backend_config: dict | None = get_config()
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return "", ""

    raw_name, rpl_name = get_raw_rpl_names(data_source)
    # get the path to the raw data in the server
    path_to_raw: str = join(
        backend_config["uploads-folder"], data_source, raw_name)

    # get the path to the rpl file in the server
    path_to_rpl: str = join(
        backend_config["uploads-folder"], data_source, rpl_name)

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
            # first split on linebreak
            info: list[str] = in_file.read().splitlines()
    except OSError as err:
        LOG.error("error while reading rpl file: {%s}", err)
        return {}

    parsed_rpl: dict[str, str] = {}
    if info:
        for line in info:
            split: list[str] = line.split()  # split on whitespace
            if len(split) == 2:
                # add tuple to dictionary
                parsed_rpl[split[0].strip()] = split[1].strip()
    else:
        LOG.error("Error while parsing rpl file: file empty")

    return parsed_rpl


def set_binned(data_source: str, binned: bool):
    """
    Sets the binned boolean attribute of a workspace.

    :param data_source: Name of the data source.
    :param binned: Boolean to set binned to.
    """
    workspace_dict: dict | None = get_workspace_dict(data_source)
    if workspace_dict is None:
        raise FileNotFoundError
    if binned:
        workspace_dict["spectralParams"]["binned"] = True
    else:
        workspace_dict["spectralParams"]["binned"] = False

    workspace_path = get_path_to_workspace(data_source)

    with open(workspace_path, 'w') as f:
        json.dump(workspace_dict, f)


def get_spectra_params(data_source: str) -> dict[str, int]:
    """
    Returns the spectrum parameters (low/high boundaries and bin size) of a data source.

    :param data_source: Name of the data source.
    :return: dictionary with the low, high and bin size values
    """
    workspace_dict: dict | None = get_workspace_dict(data_source)
    if workspace_dict is None:
        raise FileNotFoundError

    return workspace_dict["spectralParams"]


def get_workspace_dict(data_source_folder_name: str) -> dict | None:
    """
    Returns the workspace of the specified data source in dictionary format.

    :param data_source_folder_name: Name of the data source folder.
    :return: Dictionary format of the workspace.json
    """
    backend_config: dict | None = get_config()

    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return None

    workspace_json_dir = join(
        backend_config["uploads-folder"], data_source_folder_name, "workspace.json"
    )
    try:
        with open(workspace_json_dir, "r") as workspace:
            workspace_json = json.loads(workspace.read())
            return workspace_json
    except Exception:
        LOG.error(
            f"Error while reading workspace json of data source with folder name {
                data_source_folder_name}"
        )
        return None


def get_cube_recipe_path(data_source_folder_name: str) -> str | None:
    """
    Returns the path of the data cube recipe of the specified data source. If the data cube does
    not have a recipe, the function returns None.

    :param data_source_folder_name: Name of the data source folder.
    :return: Path of the data cube recipe
    """
    # load backend config
    backend_config: dict | None = get_config()
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return None

    workspace_dict: dict = get_workspace_dict(data_source_folder_name)

    if workspace_dict is None:
        return None

    recipe_name: str = workspace_dict["elementalCubes"][0]["recipeLocation"]

    if recipe_name == "":
        return None

    recipe_path: str = join(
        backend_config["uploads-folder"],
        data_source_folder_name,
        recipe_name,
    )

    return recipe_path


def get_base_image_name(data_source_folder_name: str) -> str | None:
    """Get the name of the rgb image of a given data source.

    :param data_source_folder_name: Name of the data source folder.
    :return: Name of the rgb image.
    """
    # load backend config
    backend_config: dict | None = get_config()
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return None

    workspace_dict: dict = get_workspace_dict(data_source_folder_name)
    if workspace_dict is None:
        return None

    return workspace_dict["baseImage"]["name"]


def get_base_image_path(data_source_folder_name: str) -> str | None:
    """Get the path to rgb image of a data source.

    :param data_source_folder_name: Name of the data source folder.
    :return: Path to the rgb image.
    """
    # load backend config
    backend_config: dict | None = get_config()
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return None

    workspace_dict: dict = get_workspace_dict(data_source_folder_name)
    if workspace_dict is None:
        return None

    filename: str | None = workspace_dict["baseImage"]["imageLocation"]

    if filename is not None:
        return join(backend_config["uploads-folder"], data_source_folder_name, filename)

    return None
