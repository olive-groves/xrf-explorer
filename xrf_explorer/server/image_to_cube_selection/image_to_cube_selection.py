from xrf_explorer.server.file_system.elemental_cube import get_elemental_data_cube
from xrf_explorer.server.file_system.file_access import (
    get_elemental_cube_path,
    get_rgb_path,
)
from cv2 import imread
import numpy as np
import logging

LOG: logging.Logger = logging.getLogger(__name__)


def get_sliced_data_cube(
    data_cube: np.ndarray,
    selection_coord_1: tuple[int, int],
    selection_coord_2: tuple[int, int],
) -> np.ndarray:
    """
    Extracts and returns a rectangular region from the specified data cube. This rectangular region is specified by the
    two diagonal corners - selection_coord_1 and selection_coord_2.

    :param data_cube: The data cube.
    :param selection_coord_1: The first coordinate tuple (x1, y1), representing one corner of the rectangular region.
    :param selection_coord_2: The second coordinate tuple (x2, y2), representing the opposite corner of the rectangular region.
    :return: A numpy array containing the data from the defined rectangular region within the original data cube.

    """
    x1, y1 = selection_coord_1
    x2, y2 = selection_coord_2

    # We implement the case distinction
    x_min, x_max = sorted([x1, x2])
    y_min, y_max = sorted([y1, y2])

    return data_cube[:, y_min:y_max, x_min:x_max]


def get_cube_coordinates(
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
    config_path="config/backend.yml",
) -> np.ndarray | None:
    """
    Extracts and returns a region of a data cube, based on the rectangular selection coordinates on the base image.

    :param data_source_name: The data source folder name.
    :param selection_coord_1: The first coordinate tuple (x1, y1), representing one corner of the rectangular region in the base image.
    :param selection_coord_2: The second coordinate tuple (x2, y2), representing the opposite corner of the rectangular region in the base image.
    :return: A numpy array containing the selected cube data or None if data source directory is not found.
    """
    cube_dir: str | None = get_elemental_cube_path(data_source_folder_name, config_path)

    if cube_dir is None:
        LOG.error(f"Data source directory {data_source_folder_name} does not exist.")
        return None

    base_img_dir = get_rgb_path(data_source_folder_name, config_path)

    if base_img_dir is None:
        LOG.error(
            f"Error occured while retrieving the path fo the base image of {data_source_folder_name}"
        )
        return None

    data_cube = get_elemental_data_cube(cube_dir)

    img_h, img_w, _ = imread(base_img_dir).shape
    cube_h, cube_w = data_cube.shape[1], data_cube.shape[2]

    selection_coord_1_cube, selection_coord_2_cube = get_cube_coordinates(
        selection_coord_1, selection_coord_2, img_w, img_h, cube_w, cube_h
    )

    return get_sliced_data_cube(
        data_cube, selection_coord_1_cube, selection_coord_2_cube
    )
