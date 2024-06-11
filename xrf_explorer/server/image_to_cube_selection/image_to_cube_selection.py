from xrf_explorer.server.file_system.elemental_cube import get_elemental_data_cube
from xrf_explorer.server.file_system.file_access import (
    get_elemental_cube_path,
    get_base_image_path,
    get_cube_recipe_path,
)
from cv2 import (
    imread,
    perspectiveTransform,
    getPerspectiveTransform,
    convexHull,
    fillConvexPoly,
)
from xrf_explorer.server.image_register.register_image import (
    load_points,
    compute_fitting_dimensions_by_aspect,
)
import numpy as np
import logging

LOG: logging.Logger = logging.getLogger(__name__)


def perspective_transform_coord(coord: tuple[int, int], transform_matrix: np.ndarray) -> tuple[float, float]:
    """
    Transforms the perspective of a coordinate (x, y) to (x', y') based on a transformation
    matrix.

    :param coord: The (x, y) coordinate to be transformed.
    :param transform_matrix: The transformation matrix.
    :return: A (x', y') perspective transformed coordinate.
    """
    coord_correct_format = np.array([[[coord[0], coord[1]]]], dtype="float32")

    perspective_transformed_point = perspectiveTransform(coord_correct_format, transform_matrix)
    return (
        (perspective_transformed_point[0][0][0]),
        (perspective_transformed_point[0][0][1]),
    )


def deregister_coord(
    coord: tuple[int, int],
    cube_recipe_path: str,
    base_img_height: int,
    base_img_width: int,
    cube_height: int,
    cube_width: int,
) -> tuple[int, int]:
    """
    Translates an (x, y) coordinate to its (x', y') counterpart in the cube coordinate system.
    The function assumes that the cube recipe maps cube coordinates to the base image coordinates.

    :param coord: The (x, y) coordinate to be translated.
    :param cube_recipe_path: The path to the cube recipe.
    :param base_img_height: The height of the base image in pixels.
    :param base_img_width: The width of the base image in pixels.
    :param cube_height: The height of the cube.
    :param cube_width: The width of the cube.
    :return: A (x', y') tuple representing the translated coordinate to the cube's coordinates.
    """
    # Note: Reversing padding is not needed, since the images are padded
    #       on their right and bottom sides. Since (0, 0) is at the top
    #       left corner of the image, padding does not affect the coordinate
    #       system.

    # First step: Reverse perspective transformation
    src_points, base_points = load_points(cube_recipe_path)
    transform_matrix = getPerspectiveTransform(base_points, src_points)
    x_perspective_reversed, y_perspective_reversed = perspective_transform_coord(coord, transform_matrix)

    cube_height_scaled_before_pad, registered_uv_width_before_pad = compute_fitting_dimensions_by_aspect(
        cube_height, cube_width, base_img_height, base_img_width
    )

    # Second step: Reverse scaling
    x_reversed_scaling = None
    y_reversed_scaling = None

    ratio_x = cube_width / registered_uv_width_before_pad
    ratio_y = cube_height / cube_height_scaled_before_pad

    x_reversed_scaling = x_perspective_reversed * ratio_x
    y_reversed_scaling = y_perspective_reversed * ratio_y

    return round(x_reversed_scaling), round(y_reversed_scaling)


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
        round(selection_coord_1[1] * ratio_cube_img_height),
    )
    scaled_coord_2: tuple[int, int] = (
        round(selection_coord_2[0] * ratio_cube_img_width),
        round(selection_coord_2[1] * ratio_cube_img_height),
    )

    return scaled_coord_1, scaled_coord_2


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
        LOG.error(f"Error occured while retrieving the path fo the base image of {data_source_folder}")
        return None

    data_cube: np.ndarray = get_elemental_data_cube(cube_dir)

    img_h, img_w, _ = imread(base_img_dir).shape
    cube_h, cube_w = data_cube.shape[1], data_cube.shape[2]

    cube_recipe_path: str | None = get_cube_recipe_path(data_source_folder)

    if cube_recipe_path is None:
        # If the data cube has no recipe, simply scale the selection coordinates to match the dimensions of the cube.
        selection_coord_1_cube, selection_coord_2_cube = get_scaled_cube_coordinates(
            selection_coord_1, selection_coord_2, img_w, img_h, cube_w, cube_h
        )

        x1, y1 = selection_coord_1_cube
        x2, y2 = selection_coord_2_cube

        mask: np.ndarray = np.zeros((cube_h, cube_w), dtype=bool)
        mask[y1 : y2 + 1, x1 : x2 + 1] = True

        # Note: Using selection with a boolean mask for a simple rectangular selection is not
        #       the best choice for performance, but the mask simplifies things, since it can be
        #       used for all kinds of selections to be implemented in the future.
        #       Also the performance decrease should be less than tenth of a second in most cases.
        return extract_selected_data(data_cube, mask)
    else:
        # If the data cube has recipe, deregister the selection coordinates so they correctly represent
        # the selected area on the data cube
        x1, y1 = selection_coord_1
        x2, y2 = selection_coord_2

        # Get all 4 points of the selection rectangle
        p1 = (x1, y1)
        p2 = (x1, y2)
        p3 = (x2, y1)
        p4 = (x2, y2)

        # Deregister to cube coordinates
        args = (cube_recipe_path, img_h, img_w, cube_h, cube_w)
        p1_cube = deregister_coord(p1, *args)
        p2_cube = deregister_coord(p2, *args)
        p3_cube = deregister_coord(p3, *args)
        p4_cube = deregister_coord(p4, *args)

        cube_points = np.array([p1_cube, p2_cube, p3_cube, p4_cube])
        mask = np.zeros((cube_h, cube_w), dtype=np.uint8)

        # Calculate the smallest convex set that contains all the points
        # The purpose of this is to to order the points so they construct a polygon instead
        # of an hourglass figure
        convex_hull = convexHull(cube_points)

        # Write 1's in the polygon area
        fillConvexPoly(mask, convex_hull, (1,))

        mask = mask.astype(bool)

        return extract_selected_data(data_cube, mask)
