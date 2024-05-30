from xrf_explorer.server.file_system.elemental_cube import get_elemental_data_cube
import json
from cv2 import imread
import numpy as np
from xrf_explorer.server.file_system.from_dms import (
    get_elemental_datacube_dimensions_from_dms,
)
from xrf_explorer.server.file_system.config_handler import load_yml
from os.path import join

BACKEND_CONFIG: dict = load_yml("config/backend.yml")


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

    ratio_cube_img_width = cube_width / base_img_width
    ratio_cube_img_height = cube_height / base_img_height

    x_1_new = round(x_1 * ratio_cube_img_width)
    x_2_new = round(x_2 * ratio_cube_img_width)
    y_1_new = round(y_1 * ratio_cube_img_height)
    y_2_new = round(y_2 * ratio_cube_img_height)

    # Let's assume the cube has exactly 2 times smaller height and the same width
    # And a seelction is makde (0, 0) and (500, 300)
    # then ratio_img_cube_height = 2
    # and then y_1_new and y_2_new become 0 and 600

    return (x_1_new, y_1_new), (x_2_new, y_2_new)


def get_selected_data_cube(
    data_source_folder_name: str,
    selection_coord_1: tuple[int, int],
    selection_coord_2: tuple[int, int],
) -> np.ndarray:
    data_source_dir = join(BACKEND_CONFIG["uploads-folder"], data_source_folder_name)

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
