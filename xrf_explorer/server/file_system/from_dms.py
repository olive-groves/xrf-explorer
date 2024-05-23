import logging

from os.path import isfile
from pathlib import Path

import numpy as np

LOG: logging.Logger = logging.getLogger(__name__)


def get_elemental_datacube_dimensions_from_dms(path: str | Path) \
        -> tuple[int, int, int, int]:
    """Get the dimensions of the elemental datacube. Error can be raised if
    file could not be read.
    
    :param path_to_raw_data: Path to the raw data file in the server.
    :param config_path: Path to the backend config file
    :return: 4-tuple of the dimensions of the raw elemental data and the header size (in bytes).
    Tuple is as follows (width, height, channels, header size)
    """
    
    with open(path, 'rb') as file:
        # Read the first line and ignore it (doesn't include important data)
        file.readline()

        # Read the second line
        dimensions_list: list[str] = file.readline().decode('ascii').strip().split()
        
        # Parse the second line into the dimensions
        dimensions = [int(dim) for dim in dimensions_list]

        # Save the size of the header
        header_size = file.tell()

        return (*dimensions, header_size)


def get_elements_from_dms(path: str | Path) -> list[str]:
    """Get the names of the elements stored in the elemental data cube.
    
    :param path: Path to the dms file containing the elemental data cube.
    :return: List of the names of the elements. Empty list if error occured.
    """
    
    LOG.info(f"Reading elements from {path}")

    # Check if the file exists
    if not isfile(path):
        LOG.error(f"File not found: {path}")
        return []
    
    # data dimensions
    try:
        (width, height, channels, header_size) = get_elemental_datacube_dimensions_from_dms(path)
    except Exception as e:
        LOG.error(f"Could not read elemental data file: {str(e)}")
        return []
    
    try:
        with open(path, 'rb') as f:
            # Calculate total offset 
            total_offset: int = header_size + width * height * channels * 4

            # Go to elemental names
            f.seek(total_offset)

            # Read all element names
            names: list[str] = []
            while line := f.readline():
                names.append(line.decode('utf-8').strip().replace(" ", ""))
            
            return names
    except Exception as e:
        LOG.error(f"Could not read elemental data file: {str(e)}")
        return []


def get_raw_elemental_data_cube_from_dms(path: str | Path) -> np.ndarray:
    """Get the elemental data cube from the csv file.

    :param path: Path to the csv file containing the elemental data cube.
    :return: 3-dimensional numpy array containing the normalized elemental data. First dimension
    is channel, and last two for x, y coordinates.
    """

    LOG.info(f"Reading elemental data cube from {path}")

    # Check if the file exists
    if not isfile(path):
        LOG.error(f"File not found: {path}")
        return []
    
    # data dimensions
    try:
        (w, h, c, header_size) = get_elemental_datacube_dimensions_from_dms(path)
    except Exception as e:
        LOG.error(f"Could not read elemental data file: {str(e)}")
        return np.empty(0)

    # convert it into a numpy array
    try:
        # list of raw elemental data
        list_raw_elemental_cube = np.fromfile(path, offset=header_size, count=w*h*c, dtype=np.float32)

        # reshape the raw elemental data
        return list_raw_elemental_cube.reshape(c, h, w)
    except Exception as e:
        LOG.error(f"Could not read elemental data file: {str(e)}")
        return np.empty(0)
