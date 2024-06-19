from xrf_explorer.server.file_system.cubes.spectral import parse_rpl
from xrf_explorer.server.file_system.workspace.file_access import (
    get_elemental_cube_path,
    get_base_image_path,
    get_raw_rpl_paths,
    get_cube_recipe_path,
)
from cv2 import fillPoly, imread, perspectiveTransform, getPerspectiveTransform, convexHull

from xrf_explorer.server.image_register.register_image import load_points, compute_fitting_dimensions_by_aspect
from enum import Enum
import numpy as np
import logging

LOG: logging.Logger = logging.getLogger(__name__)


class SelectionType(str, Enum):
    """
    An enumeration to represent different selection tools.
    
    Attributes:
        Rectangle: Represents the rectangle selection tool.
        Lasso: Represents the lasso selection tool.
    """
    Rectangle = "rectangle"     # The rectangle selection tool
    Lasso = "lasso"             # The lasso selection tool


class CubeType(Enum):
    """
    An enumeration to represent different types of datacubes.
    
    Attributes:
        Raw: Represents the raw datacube (i.e. the .raw or .rpl file)
        Elemental: Represents the elemental datacube (i.e. the .dms file)
    """
    Raw = "raw"
    Elemental = "elemental"


def perspective_transform_coord(coord: tuple[int, int], transform_matrix: np.ndarray) -> tuple[float, float]:
    """
    Transforms the perspective of a coordinate (x, y) to (x', y') based on a transformation
    matrix.

    :param coord: The (x, y) coordinate to be transformed.
    :param transform_matrix: The transformation matrix.
    :return: A (x', y') perspective transformed coordinate.
    """
    coord_correct_format: np.ndarray = np.array(
        [[[coord[0], coord[1]]]], dtype="float32")

    perspective_transformed_point: np.ndarray = perspectiveTransform(coord_correct_format, transform_matrix)
    return float(perspective_transformed_point[0][0][0]), float(perspective_transformed_point[0][0][1])


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
    src_points: np.ndarray
    base_points: np.ndarray
    src_points, base_points = load_points(cube_recipe_path)

    transform_matrix: np.ndarray = getPerspectiveTransform(
        base_points, src_points)

    x_perspective_reversed: float
    y_perspective_reversed: float
    x_perspective_reversed, y_perspective_reversed = perspective_transform_coord(
        coord, transform_matrix)

    cube_height_scaled_before_pad: int
    cube_width_scaled_before_pad: int
    cube_height_scaled_before_pad, cube_width_scaled_before_pad = compute_fitting_dimensions_by_aspect(
        cube_height, cube_width, base_img_height, base_img_width
    )

    # Second step: Reverse scaling
    x_reversed_scaling: float
    y_reversed_scaling: float

    ratio_x = cube_width / cube_width_scaled_before_pad
    ratio_y = cube_height / cube_height_scaled_before_pad

    x_reversed_scaling = x_perspective_reversed * ratio_x
    y_reversed_scaling = y_perspective_reversed * ratio_y

    return round(x_reversed_scaling), round(y_reversed_scaling)


def extract_selected_data(mask: np.ndarray, cube_type: CubeType) -> np.ndarray:
    """
    Extracts elements from a 3D data cube at positions specified by a 2D boolean mask.

    :param mask: A 2D boolean array where True indicates the position to be extracted from the last 2 dimensions of data_cube.
    :param cube_type: The type of the cube the selection is made on.
    :return: The list coordinates of indices of the selected pixels, grouped by pixel.
    """
    return np.argwhere(mask)


def get_scaled_cube_coordinates(
        coords: list[tuple[int, int]],
        base_img_width: int,
        base_img_height: int,
        cube_width: int,
        cube_height: int,
) -> list[tuple[int, int]]:
    """
    Calculates and returns the coordinates of a list of points within the data cube, scaled from the coordinates of a base image.

    :param coords:  List of points/coordinates within the data cube.
    :param base_img_width: The width of the base image in pixels.
    :param base_img_height: The height of the base image in pixels.
    :param cube_width: The width of the cube.
    :param cube_height: The height of the cube.
    :return: A list of all the scaled coordinates, in the same order as they were input.
    """
    ratio_cube_img_width: float = cube_width / base_img_width
    ratio_cube_img_height: float = cube_height / base_img_height

    scaled_coords: list[tuple[int, int]] = []

    for coord in coords:
        scaled_coord: tuple[int, int] = (
            round(coord[0] * ratio_cube_img_width),
            round(coord[1] * ratio_cube_img_height)
        )
        scaled_coords.append(scaled_coord)

    return scaled_coords


def compute_bounding_box(polygon_vertices: list[tuple[int, int]]) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Compute the smallest rectangle encapsulating every point in a polygon.

    :param polygon_vertices: List of points that make up the polygon (vertices).
    :return: The top-left and bottom-right points of the computed bounding box, in that order.
    """
    x_coords: list[int] = [point[0] for point in polygon_vertices]
    y_coords: list[int] = [point[1] for point in polygon_vertices]

    return (min(x_coords), min(y_coords)), (max(x_coords), max(y_coords))


def clip_points(points: list[tuple[int, int]], cube_width: int, cube_height: int) -> list[tuple[int, int]]:
    """
    Clip a list of points to the bounds of the datacube.

    :param points: A list of points where each point is a tuple (x, y).
    :param cube_width: The width of the datacube corresponding to the painting.
    :param cube_height: The height of the datacube corresponding to the painting.
    :return: The list of clipped points, in the same order as the input.
    """
    clipped_points = []

    for x, y in points:
        clipped_x = max(0, min(x, cube_width - 1))   # -1 for 0 based indexing
        clipped_y = max(0, min(y, cube_height - 1))
        clipped_points.append((clipped_x, clipped_y))

    return clipped_points


def compute_selection_mask(
        selection_type: SelectionType,
        selection: list[tuple[int, int]],
        cube_width: int,
        cube_height: int):
    """
    Compute the selection mask of a given selection.
    
    :param selection_type: The type of selection the mask being computed is for.
    :param selection: List of points that define the selection.
    :param cube_width: Width of the elemental datacube.
    :param cube_height: Height of the elemental datacube.
    :return: 2D mask of the datacube, where mask[y, x]==True means the point at (x, y) is in the selection,
    False means it is not.
    """
    mask: np.ndarray = np.zeros((cube_height, cube_width), dtype=np.uint8)

    np_selection: np.ndarray = np.array(selection)
    
    # If the selection is Rectangle selection, the polygon cannot self intersect,
    # so find the convex hull of the selection
    if selection_type == SelectionType.Rectangle:
        # Calculate the smallest convex set that contains all the points
        # The purpose of this is to order the points so they construct a polygon instead
        # of an hourglass figure
        x1, y1 = np_selection[0]
        x2, y2 = np_selection[1]
        
        p1 = (x1, y1)
        p2 = (x1, y2)
        p3 = (x2, y1)
        p4 = (x2, y2)

        np_selection = convexHull(np.array([p1, p2, p3, p4]))

    # Write 1's in the polygon area
    # Takes into account the weird shapes that can occur if the points are
    # in different order
    fillPoly(mask, [np_selection], (1,))

    return mask.astype(bool)


def get_selection(
        data_source_folder: str,
        selection_coords: list[tuple[int, int]],
        selection_type: SelectionType,
        cube_type: CubeType
) -> np.ndarray | None:
    """
    Extracts and returns a 2D representation of a data cube region, based on the selection coordinates
    on the base image. If the specified data source contains a recipe for the data cube, the selection made on the
    base image is "deregistered" so that the returned data from the function correctly represents the selected
    pixels on the image. If the data cube does not have a recipe, the selection made on the base image is simply
    scaled to match the data cube's dimensions.

    :param data_source_folder: The data source folder name.
    :param selection_coords: The coordinates tuples (x, y), in order, of the selection. In case of a rectangle 
    :param selection_type: The type of selection being performed. selection, the list must contain the two opposite corners of the selection rectangle. In case of lasso selection, the list must contain the points in the order in which they form the selection area.
    :param cube_type: The type of the cube the selection is made on.
    :return: A boolean mask over the data cube indicating which pixels are part of the selection.
    """
    if selection_type == SelectionType.Rectangle and len(selection_coords) != 2:
        LOG.error(f"Expected 2 points for rectangle selection but got {len(selection_coords)}")
        return None

    if selection_type == SelectionType.Lasso and len(selection_coords) < 3:
        LOG.error(f"Expected at least 3 points for lasso selection but got {len(selection_coords)}")
        return None

    cube_dir: str | None = None
    
    match cube_type:
        case CubeType.Elemental:
            cube_dir = get_elemental_cube_path(data_source_folder)
        case CubeType.Raw:
            cube_dir = get_raw_rpl_paths(data_source_folder)[0] 
        case _:
            LOG.error(f"Incorrect cube type: {cube_type}")
            return None

    if cube_dir is None:
        LOG.error(f"Data source directory {data_source_folder} does not exist.")
        return None

    base_img_dir: str | None = get_base_image_path(data_source_folder)

    if base_img_dir is None:
        LOG.error(f"Error occurred while retrieving the path of the base image of {data_source_folder}")
        LOG.error(
            f"Error occurred while retrieving the path of the base image of {data_source_folder}"
        )
        return None

    img_h: int
    img_w: int
    cube_h: int
    cube_w: int
    img_h, img_w, _ = imread(base_img_dir).shape
    
    # get paths to files
    path_to_rpl = get_raw_rpl_paths(data_source_folder)[1]

    # get dimensions from rpl file
    info = parse_rpl(path_to_rpl)
    if not info:
        return np.empty(0)
    cube_w = int(info['width'])
    cube_h = int(info['height'])
        
    cube_recipe_path: str | None = get_cube_recipe_path(data_source_folder)

    if cube_recipe_path is None:
        # If the data cube has no recipe, simply scale the selection coordinates to match the dimensions of the cube.
        selection_coords_scaled: list[tuple[int, int]] = get_scaled_cube_coordinates(
            selection_coords, img_w, img_h, cube_w, cube_h
        )

        mask: np.ndarray = compute_selection_mask(selection_type, selection_coords_scaled, cube_w, cube_h)

        # Note: Using selection with a boolean mask for a simple rectangular selection is not
        #       the best choice for performance, but the mask simplifies things, since it can be
        #       used for all kinds of selections to be implemented in the future.
        #       Also, the performance decrease should be less than tenth of a second in most cases.
        return mask
    else:
        # If the data cube has a recipe, deregister the selection coordinates so they correctly represent
        # the selected area on the data cube
        args = (cube_recipe_path, img_h, img_w, cube_h, cube_w)
        selection_coords_deregistered: list[tuple[int, int]] = []
        for coord in selection_coords:
            coord_deregistered: tuple[int, int] = deregister_coord(coord, *args)
            selection_coords_deregistered.append(coord_deregistered)

        mask: np.ndarray = compute_selection_mask(selection_type, selection_coords_deregistered, cube_w, cube_h)

        return mask
