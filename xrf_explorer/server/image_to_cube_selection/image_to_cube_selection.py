from xrf_explorer.server.file_system.elemental_cube import get_elemental_data_cube
from cv2 import imread
import numpy as np
from xrf_explorer.server.file_system.from_dms import (
    get_elemental_datacube_dimensions_from_dms,
)
from os.path import join, exists
import logging
import json

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
    data_source_dir: str,
    selection_coord_1: tuple[int, int],
    selection_coord_2: tuple[int, int],
) -> np.ndarray:
    """
    Extracts and returns a region of a data cube, based on the rectangular selection coordinates on the base image.

    :param data_source_dir: The data source directory.
    which can be derived using werkzeug.utils.secure_filename(data_source_name).
    :param selection_coord_1: The first coordinate tuple (x1, y1), representing one corner of the rectangular region in the base image.
    :param selection_coord_2: The second coordinate tuple (x2, y2), representing the opposite corner of the rectangular region in the base image.
    :return: A numpy array containing the selected cube data.
    """

    if not exists(data_source_dir):
        LOG.error(f"Data source directory {data_source_dir} does not exist.")

    file = open(join(data_source_dir, "workspace.json"))
    workspace_json = json.loads(file.read())
    file.close()

    base_img_name = workspace_json["baseImage"]["location"]
    # NOTE we assume a single, full dms cube here. Refactor when stiching multiple dms
    # files gets implemented
    cube_name = workspace_json["elementalCubes"][0]["dmsLocation"]

    img_h, img_w, _ = imread(f"{data_source_dir}/{base_img_name}").shape
    cube_w, cube_h, _, _ = get_elemental_datacube_dimensions_from_dms(
        join(data_source_dir, cube_name)
    )

    data_cube = get_elemental_data_cube(cube_name)

    selection_coord_1_cube, selection_coord_2_cube = get_cube_coordinates(
        selection_coord_1, selection_coord_2, img_w, img_h, cube_w, cube_h
    )

    return get_sliced_data_cube(
        data_cube, selection_coord_1_cube, selection_coord_2_cube
    )
