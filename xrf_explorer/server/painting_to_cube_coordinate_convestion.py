from xrf_explorer.server.file_system.elemental_cube import get_elemental_data_cube
import json
from cv2 import imread
import numpy as np
from xrf_explorer.server.file_system.from_dms import (
    get_elemental_datacube_dimensions_from_dms,
)


def get_sliced_data_cube(data_cube, selection_coord_1, selection_coord_2):
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
    x_1, y_1 = selection_coord_1
    x_2, y_2 = selection_coord_2

    ratio_img_cube_width = base_img_width / cube_width
    ratio_img_cube_height = base_img_height / cube_height

    x_1_new = round(x_1 * ratio_img_cube_width)
    x_2_new = round(x_2 * ratio_img_cube_width)
    y_1_new = round(y_1 * ratio_img_cube_height)
    y_2_new = round(y_2 * ratio_img_cube_height)

    return (x_1_new, y_1_new), (x_2_new, y_2_new)


def get_selected_data_cube(
    data_source_name: str,
    selection_coord_1: tuple[int, int],
    selection_coord_2: tuple[int, int],
) -> np.ndarray:
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

    selection_coord_1_cube, selection_coord_2_cube = get_cube_coordinates(
        selection_coord_1, selection_coord_2, img_w, img_h, cube_w, cube_h
    )

    return get_sliced_data_cube(
        data_cube, selection_coord_1_cube, selection_coord_2_cube
    )
