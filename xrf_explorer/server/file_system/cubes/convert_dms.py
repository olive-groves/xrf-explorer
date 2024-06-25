from logging import Logger, getLogger
from os.path import isdir, join
from pathlib import Path

import numpy as np

from xrf_explorer.server.file_system import data_source_name_from_cube_path
from xrf_explorer.server.file_system.workspace import get_elemental_cube_path

LOG: Logger = getLogger(__name__)


def get_elemental_datacube_dimensions(data_source: str) -> tuple[int, int, int, int] | None:
    """Get the dimensions of the elemental datacube. Error can be raised if
    file could not be read.
    
    :param data_source: Name of the data source containing the raw data file in the server
    :return: 4-tuple of the dimensions of the raw elemental data and the header size (in bytes). Tuple is as follows (width, height, channels, header size)
    """

    cube_path: str | None = get_elemental_cube_path(data_source)
    if cube_path is None:
        LOG.error(f"Could not retrieve the dimensions of the data cube at {data_source}")
        return None

    with open(cube_path, 'rb') as file:
        # Read the first line and ignore it (doesn't include important data)
        file.readline()

        # Read the second line
        dimensions_list: list[str] = file.readline().decode('ascii').strip().split()

        # Parse the second line into the dimensions
        dimensions: list[int] = [int(dim) for dim in dimensions_list]

        # Save the size of the header
        header_size: int = file.tell()

        return (*dimensions, header_size)


def get_elements_from_dms(path: str | Path) -> list[str]:
    """Get the names of the elements stored in the elemental data cube.
    Can raise error if file could not be read.
    
    :param path: Path to the dms file containing the elemental data cube.
    :return: List of the names of the elements.
    """

    # data dimensions
    data_source: str = data_source_name_from_cube_path(path)
    (width, height, channels, header_size) = get_elemental_datacube_dimensions(data_source)

    with open(path, 'rb') as f:
        # Calculate total offset 
        total_offset: int = header_size + width * height * channels * 4

        # Go to elemental names
        f.seek(total_offset)

        # Read all element names
        names: list[str] = []
        while line := f.readline():
            names.append(line.decode('utf-8').strip())

        return names


def get_elemental_data_cube_from_dms(path: str | Path) -> np.ndarray:
    """Get the elemental data cube from the dms file.
    Can raise error if file could not be read.

    :param path: Path to the dms file containing the elemental data cube.
    :return: 3-dimensional numpy array containing the elemental data cube. First dimension is channel, and last two for x, y coordinates
    """

    # get data dimensions
    data_source: str = data_source_name_from_cube_path(path)
    dimensions: tuple[int, int, int, int] | None = get_elemental_datacube_dimensions(data_source)
    if dimensions is None:
        LOG.error("Could not get elemental datacube dimensions")
        return np.empty(0)
    (w, h, c, header_size) = dimensions

    # list of raw elemental data
    list_raw_elemental_cube: np.ndarray = np.fromfile(path, offset=header_size, count=w * h * c, dtype=np.float32)

    # reshape the raw elemental data
    return list_raw_elemental_cube.reshape(c, h, w)


def get_elemental_map_from_dms(element: int, path: str | Path) -> np.ndarray:
    """Get the elemental map of the given element from the dms file.
    Can raise error if file could not be read.

    :param element: Index of the element in the elemental data cube.
    :param path: Path to the dms file containing the elemental data cube.
    :return: 2-dimensional numpy array containing the elemental map. Dimensions are the x, y coordinates.
    """

    # get data dimensions
    data_source: str = data_source_name_from_cube_path(path)
    (w, h, _, header_size) = get_elemental_datacube_dimensions(data_source)

    # size of the elemental map in bytes
    bytes_elemental_map: int = w * h * 4

    # total offset to the beginning of the elemental map
    total_offset: int = header_size + element * bytes_elemental_map

    # list of raw elemental map
    list_raw_elemental_cube: np.ndarray = np.fromfile(path, offset=total_offset, count=w * h, dtype=np.float32)

    # reshape the raw elemental map
    return list_raw_elemental_cube.reshape(h, w)


def to_dms(folder_path: str, name_cube: str, cube: np.ndarray, elements: list[str]) -> bool:
    """Saves a numpy array and list of elements to a DMS file.

    :param folder_path: Path to the folder where the DMS file will be saved.
    :param name_cube: Name of the elemental data cube. Without file extension, e.g. 'cube'.
    :param cube: 3-dimensional numpy array containing the elemental data cube. First dimension is channel, and last two for x, y coordinates.
    :param elements: List of the names of the elements.
    :return: True if the cube was saved successfully, False otherwise.
    """

    if not isdir(folder_path):
        LOG.error(f"Folder {folder_path} does not exist.")
        return False

    if "." in name_cube:
        LOG.error("Name of the cube should not contain a file extension.")
        return False

    path_cube: str = join(folder_path, name_cube + '.dms')

    # Get the shape of the elemental data cube
    c, h, w = cube.shape

    # Write the elemental data cube to a DMS file
    try:
        with open(path_cube, 'wb+') as f:
            f.write(b'2\n')
            f.write("{0} {1} {2}\n".format(w, h, c).encode())
            f.write(cube.tobytes())
            f.write('\n'.join(elements).encode())
    except OSError as e:
        LOG.error(f"Error while writing elemental map to dms: {e}")
        return False

    return True
