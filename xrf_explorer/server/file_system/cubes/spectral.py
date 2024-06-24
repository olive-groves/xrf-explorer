from logging import Logger, getLogger
from math import ceil, floor
from os import makedirs
from os.path import join, isfile, isdir

import numpy as np
import json

from xrf_explorer.server.file_system import get_path_to_generated_folder
from xrf_explorer.server.file_system.workspace import (
    get_raw_rpl_paths,
    get_workspace_dict,
    get_raw_rpl_names,
    set_binned
)
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


def mipmap_exists(data_source: str, level: int) -> bool:
    """Checks if a specific mipmap level exists for a data source.

    :param data_source: The datasource to check
    :param level: The mipmap level to check
    :return: Whether the specified mipmap level exists
    """

    if level <= 0:
        return True

    raw_name, _ = get_raw_rpl_names(data_source)

    # Get the path to the generated folder
    path_to_generated_folder: str = get_path_to_generated_folder(data_source)
    if not path_to_generated_folder:
        return False

    mipmap_path: str = str(join(path_to_generated_folder, "mipmaps", str(level), raw_name))

    return isfile(mipmap_path)


def mipmap_raw_cube(data_source: str, level: int):
    """Generates the mipmaps of the raw data in the data source up to the selected level.

    :param data_source: The data source to mipmap the data for
    :param level: The level to mipmap the data to, 0 is original resolution
    """
    if level <= 0:
        return

    if not mipmap_exists(data_source, level - 1):
        mipmap_raw_cube(data_source, level - 1)

    raw_name, _ = get_raw_rpl_names(data_source)

    LOG.info("Mipmapping spectral cube %s to level %i", raw_name, level)

    # Get the path to the generated folder
    path_to_generated_folder: str = get_path_to_generated_folder(data_source)
    if not path_to_generated_folder:
        return

    mipmap_dir: str = join(path_to_generated_folder, "mipmaps", str(level))
    mipmap_path: str = join(mipmap_dir, raw_name)

    # Create directory for mipmap
    if not isdir(mipmap_dir):
        makedirs(mipmap_dir)

    # Get raw data from previous mipmap
    data: np.ndarray = get_raw_data(data_source, level - 1)

    mipmapped: np.memmap = np.memmap(
        mipmap_path,
        shape=(ceil(data.shape[0] / 2.0), ceil(data.shape[1] / 2.0), data.shape[2]),
        dtype=np.uint16,
        mode="w+"
    )

    for y in range(mipmapped.shape[0]):
        for x in range(mipmapped.shape[1]):
            mipmapped[y, x, :] = np.mean(data[2 * y:2 * y + 2, 2 * x:2 * x + 2, :], axis=(0, 1))

    # Write to disk
    mipmapped.flush()

    LOG.info("Finished mipmapping spectral cube %s to level %i", raw_name, level)


def get_raw_data(data_source: str, level: int = 0) -> np.memmap | np.ndarray:
    """Parse the raw data cube of a data source as a 3-dimensional numpy array.

    :param data_source: the path to the .raw file
    :param level: the mipmap level of the data to get
    :return: memory map of the 3-dimensional array containing the raw data in format {x, y, channel}
    """
    # get paths to files
    path_to_raw, path_to_rpl = get_raw_rpl_paths(data_source)

    # get dimensions from rpl file
    info = parse_rpl(path_to_rpl)
    if not info:
        return np.empty(0)
    width: int = ceil(int(info['width']) / (2 ** level))
    height: int = ceil(int(info['height']) / (2 ** level))

    # get mipmapped cube
    if level > 0:
        if not mipmap_exists(data_source, level):
            mipmap_raw_cube(data_source, level)
        raw_name, _ = get_raw_rpl_names(data_source)

        # Get the path to the generated folder
        path_to_generated_folder: str = get_path_to_generated_folder(data_source)
        if not path_to_generated_folder:
            return np.array([])

        # Get path to raw file
        path_to_raw: str = join(path_to_generated_folder, "mipmaps", str(level), raw_name)

    try:
        params: dict = get_spectra_params(data_source)
    except FileNotFoundError as err:
        LOG.error(
            "error while loading workspace to retrieve spectra params: {%s}", err)
        return np.array([])

    low: int = params["low"]
    high: int = params["high"]
    bin_size: int = params["binSize"]
    bin_nr: int = ceil((high - low) / bin_size)

    try:
        # load raw file and parse it as 3d array with correct dimensions
        datacube: np.memmap = np.memmap(path_to_raw, dtype=np.uint16, mode='r', shape=(height, width, bin_nr))
    except OSError as err:
        LOG.error("error while loading raw file: {%s}", err)
        return np.empty(0)
    return datacube


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


def bin_data(data_source: str, low: int, high: int, bin_size: int):
    """Reduces the raw data of a data source to channels in range [low:high] and averages channels per bin.

    :param data_source: the name of the data source containing the raw data
    :param low: the lower channel boundary
    :param high: the higher channel boundary
    :param bin_size: the number of channels per bin
    """
    # get paths to files
    path_to_raw: str
    path_to_rpl: str
    path_to_raw, path_to_rpl = get_raw_rpl_paths(data_source)

    # get dimensions from rpl file
    info = parse_rpl(path_to_rpl)
    if not info:
        return np.empty(0)
    # get dimensions of original data
    width: int = int(info['width'])
    height: int = int(info['height'])
    channels: int = int(info['depth'])

    # if default settings, don't do anything
    if low == 0 and high == 4096 and bin_size == 1:
        set_binned(data_source, True)
        return

    try:
        # load raw file and parse it as 3d array with correct dimensions
        datacube: np.ndarray = np.fromfile(path_to_raw, dtype=np.uint16)
    except OSError as err:
        LOG.error("error while loading raw file for binning: {%s}", err)
        raise
    datacube: np.ndarray = np.reshape(datacube, (height, width, channels))
    # if we just need to crop
    if bin_size == 1:
        new_cube: np.ndarray = datacube[:, :, low:high]
    else:
        # compute number of bins
        nr_bins: int = ceil((high - low) / bin_size)
        # initialize  array
        new_cube: np.ndarray = np.zeros(
            shape=(height, width, nr_bins), dtype=np.int16)

        for i in range(nr_bins):
            # convert bin number to start channel in original data (i.e. in range [0, 4096])
            start_channel = low + i * bin_size
            bin_average = np.mean(
                datacube[:, :, start_channel:start_channel + bin_size], axis=2)
            new_cube[:, :, i] = bin_average

    # overwrite file
    try:
        new_cube.flatten().tofile(path_to_raw)
    except Exception as e:
        LOG.error("Failed to write binned data: {%s}", e)
    set_binned(data_source, True)


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
    
    increment: float = (40 - offset) / 4096
    workspace_dict["spectralParams"]["low"] = floor((low - offset) / increment)
    workspace_dict["spectralParams"]["high"] = ceil((high - offset) / increment)
    workspace_dict["spectralParams"]["binSize"] = round(bin_size / increment)
    
    workspace_path = get_path_to_workspace(data_source)

    with open(workspace_path, 'w') as f:
        json.dump(workspace_dict, f)
