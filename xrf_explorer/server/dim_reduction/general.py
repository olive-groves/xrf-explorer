import logging 

import numpy as np

LOG: logging.Logger = logging.getLogger(__name__)


def valid_element(element: int, data_cube: np.ndarray) -> bool:
    """Verifies whether the given element is valid for the given data cube.
    
    :param element: The element to verify.
    :param data_cube: The data cube to verify the element for.
    :return: True if the element is valid, otherwise False.
    """

    # verify valid element
    total_number_of_elements: int = data_cube.shape[0]

    if element < 0 or element >= total_number_of_elements:
        LOG.error(f"Invalid element: {element}")
        return False
    
    return True
