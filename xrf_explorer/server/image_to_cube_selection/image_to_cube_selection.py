from xrf_explorer.server.file_system.elemental_cube import get_elemental_data_cube
from xrf_explorer.server.file_system.file_access import (
    get_elemental_cube_path,
    get_base_image_path,
    get_cube_recipe_path,
)
from cv2 import imread
import numpy as np
import logging

LOG: logging.Logger = logging.getLogger(__name__)


def extract_selected_data(data_cube, mask) -> np.ndarray:
    """
    Extracts elements from a 3D data cube at positions specified by a 2D boolean mask.

    :param data_cube: The 3D data cube from which data will be extracted.
    :param mask: A 2D boolean array where True indicates the position to be extracted from the last 2 dimensions of data_cube.
    :return: A 2D array where the rows represent pixels in the data cube image and the columns represent their elemental map values.
    """
    indices = np.where(mask)
    return data_cube[:, indices[0], indices[1]]


def get_scaled_cube_coordinates(
    selection_coord_1: tuple[int, int],
    selection_coord_2: tuple[int, int],
    base_img_width: int,
    base_img_height: int,
    cube_width: int,
    cube_height: int,
) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Calculates and returns the coordinates of a rectangular region within the data cube, scaled from the coordinates of a base image.

    :param selection_coord_1: The first coordinate tuple (x1, y1), representing one corner of the rectangular region in the base image.
    :param selection_coord_2: The second coordinate tuple (x2, y2), representing the opposite corner of the rectangular region in the base image.
    :param base_img_width: The width of the base image in pixels.
    :param base_img_height: The height of the base image in pixels.
    :param cube_width: The width of the cube.
    :param cube_height: The height of the cube.
    :return: A tuple containing two tuples, representing the scaled coordinates.
    """
    x_1, y_1 = selection_coord_1
    x_2, y_2 = selection_coord_2

    ratio_cube_img_width = cube_width / base_img_width
    ratio_cube_img_height = cube_height / base_img_height

    x_1_new = round(x_1 * ratio_cube_img_width)
    x_2_new = round(x_2 * ratio_cube_img_width)
    y_1_new = round(y_1 * ratio_cube_img_height)
    y_2_new = round(y_2 * ratio_cube_img_height)

    return (x_1_new, y_1_new), (x_2_new, y_2_new)


def get_selected_data_cube(
    data_source_folder_name: str,
    selection_coord_1: tuple[int, int],
    selection_coord_2: tuple[int, int],
) -> np.ndarray | None:
    """
    Extracts and returns a 2D representation of a data cube region, based on the rectangular selection coordinates on the base image. If the specified
    data source contains a recipe for the data cube, the selection made on the base image is "deregistered" so that the returned data from the function
    correctly represents the selected pixels on the image. If the data cube does not have a recipe, the selection made on the base image is simply scaled to
    match the data cube's dimensions.

    :param data_source_name: The data source folder name.
    :param selection_coord_1: The first coordinate tuple (x1, y1), representing one corner of the rectangular region in the base image.
    :param selection_coord_2: The second coordinate tuple (x2, y2), representing the opposite corner of the rectangular region in the base image.
    :return: A 2D array where the rows represent the selected pixels from the data cube image and the columns represent their elemental map values.
    """
    cube_dir: str | None = get_elemental_cube_path(data_source_folder_name)

    if cube_dir is None:
        LOG.error(f"Data source directory {data_source_folder_name} does not exist.")
        return None

    base_img_dir: str | None = get_base_image_path(data_source_folder_name)

    if base_img_dir is None:
        LOG.error(
            f"Error occured while retrieving the path fo the base image of {data_source_folder_name}"
        )
        return None

    data_cube = get_elemental_data_cube(cube_dir)

    img_h, img_w, _ = imread(base_img_dir).shape
    cube_h, cube_w = data_cube.shape[1], data_cube.shape[2]

    cube_recipe_path = get_cube_recipe_path(data_source_folder_name)

    if (cube_recipe_path is None) or True:
        # If the data cube has no recipe, then simply scale the selection coordinates to match the dimensions of the cube.
        selection_coord_1_cube, selection_coord_2_cube = get_scaled_cube_coordinates(
            selection_coord_1, selection_coord_2, img_w, img_h, cube_w, cube_h
        )

        x1, y1 = selection_coord_1_cube
        x2, y2 = selection_coord_2_cube

        mask = np.zeros((cube_h, cube_w), dtype=bool)
        mask[y1 : y2 + 1, x1 : x2 + 1] = True

        # Note: Using selection with a boolean mask for a simple rectangular selection is not the best choice for performance
        #       But the mask simplifies things, since it can be used for all kinds of selections to be implemented in the future.
        #       And the performance decrease should be less than tenth of a second in most cases.
        return extract_selected_data(data_cube, mask)
    else:
        # If the data cube has recipe, deregister the selection coordinates so they correctly represent the selected area on the data cube
        # TODO: Implement the deregisration logic
        return np.array([])
