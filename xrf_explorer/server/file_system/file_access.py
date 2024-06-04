#module responsible for giving the different paths corresponding to the files of a data source

import logging

from os.path import isfile, join
from pathlib import Path

import json
import numpy as np

from xrf_explorer.server.file_system.config_handler import get_config

LOG: logging.Logger = logging.getLogger(__name__)


def get_elemental_cube_name(data_source: str) -> str:
    """Get the location of the elemental cube file of a given datasource
    
    :param datasource: Name of the datasource.
    :return: Path string pointing to the elemental cube location.
    """
    # load backend config
    backend_config: dict = get_config()
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return ""
    
    data_source_dir = join(Path(backend_config["uploads-folder"]), data_source, "workspace.json")
    try:
        with open(data_source_dir, 'r') as workspace:
            data_json: str = workspace.read()
            data = json.loads(data_json)
            elemental_cube_name: str = data["elementalCubes"][0]["dataLocation"]
    except OSError as err:
        LOG.error("Error while getting elemental cube name: {%s}", err)
        return 400
    
    return elemental_cube_name

def get_elemental_cube_path(data_source: str) -> str:
    """Get the path to the elemental data cube of a data source.

    :param data_source: Name of the data source.
    :return: Path to the elemental data cube.
    """
    # load backend config
    backend_config: dict = get_config()
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return ""

    filename: str = get_elemental_cube_name(data_source)
    path: str = join(Path(backend_config["uploads-folder"]), data_source, filename)
    
    #raise error is the path does not exist
    if not isfile(path):
        raise OSError("Provided datasource does not have an elemental cube file")

    return path

def get_raw_rpl_names(data_source: str) -> tuple[str, str]:
    """Get the name of the raw data file (.raw) and the .rpl file of a given datasource
    
    :param datasource: Name of the datasource.
    :return: Names of the raw data and rpl files.
    """
     # load backend config
    backend_config: dict = get_config()
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return np.empty(0)
    
    data_source_dir: str = join(Path(backend_config["uploads-folder"]), data_source, "workspace.json")
    try:
        with open(data_source_dir, 'r') as workspace:
            data_json: str = workspace.read()
            data = json.loads(data_json)
            raw_data_name: str = data["spectralCubes"][0]["rawLocation"]
            rpl_name: str = data["spectralCubes"][0]["rplLocation"]
    except OSError as err:
        LOG.error("Error while getting raw and rpl file locations: {%s}", err)
        return 400
    
    return raw_data_name, rpl_name

def get_raw_rpl_paths(data_source: str) -> tuple[str, str]:
    """Get the paths to the raw data file (.raw) and the .rpl file of a given datasource
    
    :param datasource: Name of the datasource.
    :return: Paths to the raw data and rpl files.
    """
    # load backend config
    backend_config: dict = get_config()
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return np.empty(0)

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
        with open(path, 'r') as in_file:
            info = in_file.read().splitlines() #first split on linebreak
    except OSError as err:
        LOG.error("error while reading rpl file: {%s}", err)
        return {}
    
    map = {}
    if info:    
        for line in info:
            split = line.split() #split on whitespace
            if len(split) == 2:
                map[split[0].strip()] = split[1].strip() #add tuple to dictionary
    else:
        LOG.error("Error while parsing rpl file: file empty")
               
    return map