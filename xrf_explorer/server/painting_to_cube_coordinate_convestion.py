from xrf_explorer.server.file_system.elemental_cube import get_elemental_data_cube
import json
from os import getcwd
from cv2 import imread
from xrf_explorer.server.file_system.from_dms import (
    get_elemental_datacube_dimensions_from_dms,
)


def slicing(data_cube, coordinates):
    """Slice data cube with the given coordinates.

    :param data_cube: the selected data.
    :param coordinates: the two rectangle coordinates adjusted to the dimensions of the datacube.
    :return: 3-dimensional numpy array containing the sliced datacube. First dimension is channel, and last two for y, x coordinates.
    """

    # encode the coord values
    coord1, coord2 = coordinates
    x1, y1 = coord1
    x2, y2 = coord2

    # When slicing in numpy the following syntax must be followed: [ ..., small_number:big_number, ...]
    # Thus, case distinction must be implemented:
    if (x1 < x2) and (y1 < y2):
        return data_cube[:, y1:y2, x1:x2]

    elif (x1 < x2) and (y2 < y1):
        return data_cube[:, y2:y1, x1:x2]

    elif (x2 < x1) and (y1 < y2):
        return data_cube[:, y1:y2, x2:x1]

    else:
        return data_cube[:, y2:y1, x2:x1]


def get_cube_coordinates(
    rectangle_points_on_base_image: tuple[tuple[int, int], tuple[int, int]],
    base_img_width: int,
    base_img_height: int,
    cube_width: int,
    cube_height: int,
):
    """Convert main image coordinates into datacube coordinates

    :param rectangle_points_on_base_image: the two rectangle coordiantes adjusted to the base image dimensions.
    :param base_img_width: the width of base image.
    :param base_img_height: the height of base image.
    :param cube_width: the widht of datacube.
    :param cube_height: the height of datacube.

    :return: the two rectangle coordiantes adjusted to the datacube dimensions.
    """
    
    # encode the coord values
    point_1, point_2 = rectangle_points_on_base_image

    x_1, y_1 = point_1
    x_2, y_2 = point_2

    # compute the ratios
    ratio_img_cube_width = base_img_width / cube_width
    ratio_img_cube_height = base_img_height / cube_height

    # scale the coord values to the datacube dimension
    x_1_new = x_1 * ratio_img_cube_width
    x_2_new = x_2 * ratio_img_cube_width
    y_1_new = y_1 * ratio_img_cube_height
    y_2_new = y_2 * ratio_img_cube_height

    return ((x_1_new, y_1_new), (x_2_new, y_2_new))


def get_selected_data_cube(
    data_source_name: str, coordinates: tuple[tuple[int, int], tuple[int, int]]
):
    """Pipeline function that first gets datacube, gets base image and datacube dimensions and eventually do the slicing 
       on the datacube. The pipeline calls the previously defined functions of this file.

    :param data_source_name: name of the datacube
    :param coordinates: the two rectangle coordiantes adjusted to the base image dimensions.

    :return: 3-dimensional numpy array containing the sliced datacube. First dimension is channel, and last two for y, x coordinates.
    """

    # get datacube path
    data_source_dir = f"xrf_explorer/server/data/{data_source_name}"

    # reach workspace file where datacube and base image dimensions are found
    file = open(f"{data_source_dir}/workspace.json")
    workspace_json = json.loads(file.read())
    file.close()

    # get base image and datacube names as a string
    base_img_name = workspace_json["baseImage"]["location"]
    cube_name = workspace_json["elementalCubes"][0]["dmsLocation"]

    # get dimensions
    img_h, img_w, _ = imread(f"{data_source_dir}/{base_img_name}").shape
    cube_w, cube_h, _, _ = get_elemental_datacube_dimensions_from_dms(
        f"{data_source_dir}/{cube_name}"
    )

    # do scaling: from base image coords to datacube coords
    data_cube = get_elemental_data_cube(cube_name)

    # return slicing
    return slicing(data_cube, coordinates)
