import json
import numpy as np
from logging import Logger, getLogger
from math import ceil, floor

from xrf_explorer.server.file_system.workspace import get_raw_rpl_paths, get_workspace_dict
from xrf_explorer.server.file_system.workspace.workspace_handler import get_path_to_workspace

LOG: Logger = getLogger(__name__)


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


def update_bin_params(data_source: str):
    """
    Converts the low, high and binsize parameters in the workspace from energy to channel.
    
    :param data_source: Name of the data source containing the workspace to modify.
    """
    path_to_raw, path_to_rpl = get_raw_rpl_paths(data_source)

    # get dimensions from rpl file
    info = parse_rpl(path_to_rpl)
    if not info:
        return np.empty(0)
    try:
        offset: int = int(info['depthscaleorigin'])
    except:
        offset: int = 0
    
    workspace_dict: dict | None = get_workspace_dict(data_source)
    if workspace_dict is None:
        raise FileNotFoundError
    low: float = workspace_dict["spectralParams"]["low"]
    high: float = workspace_dict["spectralParams"]["high"]
    bin_size: float = workspace_dict["spectralParams"]["binSize"]
    
    increment: float = (40-offset)/4096
    workspace_dict["spectralParams"]["low"] = floor((low - offset)/increment)
    workspace_dict["spectralParams"]["high"] = ceil((high - offset)/increment)
    workspace_dict["spectralParams"]["binSize"] = round(bin_size/increment)
    
    workspace_path = get_path_to_workspace(data_source)

    with open(workspace_path, 'w') as f:
        json.dump(workspace_dict, f)
