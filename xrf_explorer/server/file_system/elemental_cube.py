import numpy as np

def normalize_ndarray_to_grayscale(array: np.ndarray) -> np.ndarray:
    """Map all values in the given array to the interval [0, 255].
    
    :param array: n-dimensional numpy array.
    :return: a copy of the array with values mapped to the interval [0, 255].
    """

    # normalize data
    (min, max) = array.min(), array.max()
    normalized_array: np.ndarray = (array - min) / (max - min)

    # obtain image of elemental abundance at every pixel of elemental image
    return np.rint(normalized_array * 255).astype(np.uint8)


def normalize_elemental_cube_total_cube(raw_cube: np.ndarray) -> np.ndarray:
    """Normalize the raw elemental data cube.

    :param raw_cube: 3-dimensional numpy array containing the normalized elemental data. First dimension
    is channel, and last two for x, y coordinates.
    :return: 3-dimensional numpy array containing the normalized elemental data. First dimension
    is channel, and last two for x, y coordinates.
    """

    return normalize_ndarray_to_grayscale(raw_cube)


def normalize_elemental_cube_per_layer(raw_cube: np.ndarray) -> np.ndarray:
    """Normalize the raw elemental data cube.

    :param raw_cube: 3-dimensional numpy array containing the normalized elemental data. First dimension
    is channel, and last two for x, y coordinates.
    :return: 3-dimensional numpy array containing the normalized elemental data. First dimension
    is channel, and last two for x, y coordinates.
    """

    normalized_cube: np.ndarray = np.zeros(raw_cube.shape, dtype=np.uint8)
    number_of_channels = raw_cube.shape[0]

    for i in range(number_of_channels):
        normalized_cube[i] = normalize_ndarray_to_grayscale(raw_cube[i])

    return normalized_cube
