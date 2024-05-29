from xrf_explorer.server.file_system.elemental_cube import get_elemental_data_cube
import json
from os import getcwd
from cv2 import imread
from xrf_explorer.server.file_system.from_dms import (
    get_elemental_datacube_dimensions_from_dms,
)


def slicing(data_cube, coordinates):
    coord1, coord2 = coordinates
    x1, y1 = coord1
    x2, y2 = coord2

    # Corner case 1: coord dimensions are right: do not surpass elemental cube maximum
    # shape of datacube: (c, h, w)
    c, h, w = data_cube.shape
    # if (y1<0) or (y2<0) or (h<y1) or (h<y2) or (x1<0) or (x2<0) or (w<x1) or (w<x2):
    #     return []

    # Corner case 2: line instead of rectangle
    # if (x1 == x2) or (y1 == y2):
    #     return []

    # We implement the case distinction
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
    point_1, point_2 = rectangle_points_on_base_image

    x_1, y_1 = point_1
    x_2, y_2 = point_2

    ratio_img_cube_width = base_img_width / cube_width
    ratio_img_cube_height = base_img_height / cube_height

    x_1_new = x_1 * ratio_img_cube_width
    x_2_new = x_2 * ratio_img_cube_width
    y_1_new = y_1 * ratio_img_cube_height
    y_2_new = y_2 * ratio_img_cube_height

    return ((x_1_new, y_1_new), (x_2_new, y_2_new))


def get_selected_data_cube(
    data_source_name: str, coordinates: tuple[tuple[int, int], tuple[int, int]]
):
    data_source_dir = f"xrf_explorer/server/data/{data_source_name}"

    file = open(f"{data_source_dir}/workspace.json")
    workspace_json = json.loads(file.read())
    file.close()

    base_img_name = workspace_json["baseImage"]["location"]
    cube_name = workspace_json["elementalCubes"][0]["dmsLocation"]

    img_h, img_w, _ = imread(f"{data_source_dir}/{base_img_name}").shape
    cube_w, cube_h, _, _ = get_elemental_datacube_dimensions_from_dms(
        f"{data_source_dir}/{cube_name}"
    )

    data_cube = get_elemental_data_cube(cube_name)

    return slicing(data_cube, coordinates)

    mapped_coordinates = get_cube_coordinates(coordinates, img_w, img_h, cube_w, cube_h)
