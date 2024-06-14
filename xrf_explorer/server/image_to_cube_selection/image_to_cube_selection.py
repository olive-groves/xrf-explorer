from xrf_explorer.server.file_system.elemental_cube import (
    get_elemental_data_cube, normalize_ndarray_to_grayscale
)
from xrf_explorer.server.file_system.file_access import (
    get_elemental_cube_path,
    get_base_image_path,
    get_cube_recipe_path,
)
from cv2 import imread
import numpy as np
import logging

LOG: logging.Logger = logging.getLogger(__name__)


def extract_selected_data(data_cube: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """
    Extracts elements from a 3D data cube at positions specified by a 2D boolean mask.

    :param data_cube: The 3D data cube from which data will be extracted.
    :param mask: A 2D boolean array where True indicates the position to be extracted
    from the last 2 dimensions of data_cube.
    :return: A 2D array where the rows represent pixels in the data cube image
    and the columns represent their elemental map values.
    """
    indices = np.nonzero(mask)
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

    :param selection_coord_1: The first coordinate tuple (x1, y1), representing
    one corner of the rectangular region in the base image.
    :param selection_coord_2: The second coordinate tuple (x2, y2), representing
    the opposite corner of the rectangular region in the base image.
    :param base_img_width: The width of the base image in pixels.
    :param base_img_height: The height of the base image in pixels.
    :param cube_width: The width of the cube.
    :param cube_height: The height of the cube.
    :return: A tuple containing two tuples, representing the scaled coordinates.
    """
    ratio_cube_img_width: float = cube_width / base_img_width
    ratio_cube_img_height: float = cube_height / base_img_height

    scaled_coord_1: tuple[int, int] = (
        round(selection_coord_1[0] * ratio_cube_img_width),
        round(selection_coord_1[1] * ratio_cube_img_height)
    )
    scaled_coord_2: tuple[int, int] = (
        round(selection_coord_2[0] * ratio_cube_img_width),
        round(selection_coord_2[1] * ratio_cube_img_height)
    )

    return scaled_coord_1, scaled_coord_2


def compute_bounding_box(polygon_vertices: list[tuple[int, int]]) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Compute the smallest rectangle encapsulating every point in a polygon.

    :param polygon_vertices: List of points that make up the polygon (vertices).
    :return: The top-left and bottom-right points of the computed bounding box, in that order.
    """
    x_coords: list[int] = [point[0] for point in polygon_vertices]
    y_coords: list[int] = [point[1] for point in polygon_vertices]

    return (min(x_coords), min(y_coords)), (max(x_coords), max(y_coords))


def is_point_in_polygon(point: tuple[int, int], polygon_vertices: list[tuple[int, int]]) -> bool:
    """
    Compute whether a given point lies in a given polygon.
    Adapted from https://www.geeksforgeeks.org/how-to-check-if-a-given-point-lies-inside-a-polygon/ .

    :param point: The point to check.
    :param polygon_vertices: The list of points that make up the polygon to check against.
    :return: True if the point lies in the polygon, false otherwise.
    """
    inside: bool = False

    poly_point_1: tuple[int, int] = polygon_vertices[0]

    for i in range(1, len(polygon_vertices) + 1):
        poly_point_2: tuple[int, int] = polygon_vertices[i % len(polygon_vertices)]

        if point[1] > min(poly_point_1[1], poly_point_2[1]) and (
                point[1] <= max(poly_point_1[1], poly_point_2[1])) and (
                point[0] <= max(poly_point_1[0], poly_point_2[0])):

            x_intersection: float = ((point[1] - poly_point_1[1]) * (poly_point_2[0] - poly_point_1[0])) / (
                    poly_point_2[1] - poly_point_1[1]) + poly_point_1[0]

            if poly_point_1[0] == poly_point_2[0] or point[0] <= x_intersection:
                inside = not inside

        poly_point_1 = poly_point_2

    return inside


def compute_selection_mask(selection_type: str, selection: list[tuple[int, int]], cube_width: int,
                           cube_height: int) -> np.ndarray:
    mask: np.ndarray = np.zeros((cube_height, cube_width), dtype=bool)

    if selection_type == "rectangle":
        x1, y1 = selection[0]
        x2, y2 = selection[1]
        mask[y1: y2 + 1, x1: x2 + 1] = True

    elif selection_type == "lasso":
        top_left, bottom_right = compute_bounding_box(selection)

        for x in range(top_left[0], bottom_right[0] + 1):
            for y in range(top_left[1], bottom_right[1] + 1):
                point: tuple[int, int] = (x, y)
                mask[y, x] = is_point_in_polygon(point, selection)

    return mask


def get_selected_data_cube(
        data_source_folder: str,
        selection_coord_1: tuple[int, int],
        selection_coord_2: tuple[int, int],
) -> np.ndarray | None:
    """
    Extracts and returns a 2D representation of a data cube region, based on the rectangular selection coordinates
    on the base image. If the specified data source contains a recipe for the data cube, the selection made on the
    base image is "deregistered" so that the returned data from the function correctly represents the selected
    pixels on the image. If the data cube does not have a recipe, the selection made on the base image is simply
    scaled to match the data cube's dimensions.

    :param data_source_folder: The data source folder name.
    :param selection_coord_1: The first coordinate tuple (x1, y1), representing one corner of the rectangular
    region in the base image.
    :param selection_coord_2: The second coordinate tuple (x2, y2), representing the opposite corner of the
    rectangular region in the base image.
    :return: A 2D array where the rows represent the selected pixels from the data cube image and the columns
    represent their elemental map values.
    """
    cube_dir: str | None = get_elemental_cube_path(data_source_folder)

    if cube_dir is None:
        LOG.error(f"Data source directory {data_source_folder} does not exist.")
        return None

    base_img_dir: str | None = get_base_image_path(data_source_folder)

    if base_img_dir is None:
        LOG.error(
            f"Error occured while retrieving the path fo the base image of {data_source_folder}"
        )
        return None

    raw_cube: np.ndarray = get_elemental_data_cube(cube_dir)
    data_cube: np.ndarray = normalize_ndarray_to_grayscale(raw_cube)

    img_h, img_w, _ = imread(base_img_dir).shape
    cube_h, cube_w = data_cube.shape[1], data_cube.shape[2]

    cube_recipe_path: str | None = get_cube_recipe_path(data_source_folder)

    if (cube_recipe_path is None) or True:
        # If the data cube has no recipe, simply scale the selection coordinates to match the dimensions of the cube.
        selection_coord_1_cube, selection_coord_2_cube = get_scaled_cube_coordinates(
            selection_coord_1, selection_coord_2, img_w, img_h, cube_w, cube_h
        )

        x1, y1 = selection_coord_1_cube
        x2, y2 = selection_coord_2_cube

        mask: np.ndarray = np.zeros((cube_h, cube_w), dtype=bool)
        mask[y1: y2 + 1, x1: x2 + 1] = True

        # Note: Using selection with a boolean mask for a simple rectangular selection is not
        #       the best choice for performance, but the mask simplifies things, since it can be 
        #       used for all kinds of selections to be implemented in the future.
        #       Also, the performance decrease should be less than tenth of a second in most cases.
        return extract_selected_data(data_cube, mask)
    else:
        # If the data cube has recipe, deregister the selection coordinates so they correctly represent 
        # the selected area on the data cube
        LOG.warning("Deregistration logic not yet implemented!")
        return np.array([])
