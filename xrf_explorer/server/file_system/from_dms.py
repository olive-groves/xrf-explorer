from pathlib import Path

import numpy as np


def get_elemental_datacube_dimensions_from_dms(path: str | Path) \
        -> tuple[int, int, int, int]:
    """Get the dimensions of the elemental datacube. Error can be raised if
    file could not be read.
    
    :param path: Path to the raw data file in the server.
    :return: 4-tuple of the dimensions of the raw elemental data and the header size (in bytes). Tuple is as follows (width, height, channels, header size)
    """
    
    with open(path, 'rb') as file:
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
    (width, height, channels, header_size) = get_elemental_datacube_dimensions_from_dms(path)
    
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
    :return: 3-dimensional numpy array containing the elemental data cube. First dimension is channel, and last two for x, y coordinates.
    """
    
    # get data dimensions
    (w, h, c, header_size) = get_elemental_datacube_dimensions_from_dms(path)

    # list of raw elemental data
    list_raw_elemental_cube: np.ndarray = np.fromfile(path, offset=header_size, count=w*h*c, dtype=np.float32)

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
    (w, h, _, header_size) = get_elemental_datacube_dimensions_from_dms(path)
    
    # size of the elemental map in bytes
    bytes_elemental_map: int = w * h * 4

    # total offset to the beginning of the elemental map
    total_offset: int = header_size + element * bytes_elemental_map

    # list of raw elemental map
    list_raw_elemental_cube: np.ndarray = np.fromfile(path, offset=total_offset, count=w*h, dtype=np.float32)
    
    # reshape the raw elemental map
    return list_raw_elemental_cube.reshape(h, w)
