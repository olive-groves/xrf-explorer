import numpy as np

import sys

from os.path import join

sys.path.append(".")

from xrf_explorer.server.file_system.file_access import (
    get_elemental_cube_path,
    get_base_image_path,
)
from xrf_explorer.server.file_system.elemental_cube import get_elemental_data_cube
from xrf_explorer.server.image_to_cube_selection import (
    get_selected_data_cube,
    get_scaled_cube_coordinates,
)
from xrf_explorer.server.file_system.config_handler import set_config
from cv2 import imread
import pytest

RESOURCES_PATH: str = join("tests", "resources")


class TestImageToCubeSelection:
    CUSTOM_CONFIG_PATH: str = join(
        RESOURCES_PATH, "configs", "image_to_cube_selection.yml"
    )
    DATA_SOURCE_FOLDER_NAME = "Data_source"

    @pytest.fixture(autouse=True)
    def setup_environment(self):
        set_config(self.CUSTOM_CONFIG_PATH)
        yield

    def test_get_selected_data_cube_dir_not_found(self, caplog):
        RGB_POINT_1: tuple[int, int] = (0, 0)
        RGB_POINT_2: tuple[int, int] = (1, 1)

        data_source_folder_name: str = "made_up_name"
        expected_output: str = (
            f"Data source directory {data_source_folder_name} does not exist."
        )

        result: np.ndarray | None = get_selected_data_cube(
            data_source_folder_name, RGB_POINT_1, RGB_POINT_2
        )

        assert result is None
        assert expected_output in caplog.text

    def test_get_selected_data_cube_dir_found(self):
        RGB_POINT_1: tuple[int, int] = (0, 0)
        RGB_POINT_2: tuple[int, int] = (1, 1)

        result: np.ndarray | None = get_selected_data_cube(
            self.DATA_SOURCE_FOLDER_NAME, RGB_POINT_1, RGB_POINT_2
        )

        assert result is not None

    def test_get_cube_coordinates(self):
        # setup
        RGB_POINT_1: tuple[int, int] = (2, 6)
        RGB_POINT_2: tuple[int, int] = (4, 10)

        data_cube_point_1_expected: tuple[int, int] = (1, 3)
        data_cube_point_2_expected: tuple[int, int] = (2, 5)

        base_image_height: int = 10
        base_image_width: int = 10
        cube_image_height: int = 5
        cube_image_width: int = 5

        # execute
        data_cube_output_1_actual, data_cube_output_2_actual = (
            get_scaled_cube_coordinates(
                RGB_POINT_1,
                RGB_POINT_2,
                base_image_width,
                base_image_height,
                cube_image_width,
                cube_image_height,
            )
        )

        # verify
        assert data_cube_output_1_actual == data_cube_point_1_expected
        assert data_cube_output_2_actual == data_cube_point_2_expected

    def test_get_selected_data_cube_output_size(self):
        # setup
        RGB_POINT_1: tuple[int, int] = (0, 0)
        RGB_POINT_2: tuple[int, int] = (345, 678)

        cube_dir: str | None = get_elemental_cube_path(self.DATA_SOURCE_FOLDER_NAME)
        print(cube_dir)

        if cube_dir is None:
            pytest.fail("Cube directory is None.")

        cube: np.ndarray = get_elemental_data_cube(cube_dir)
        _, cube_h, cube_w = cube.shape

        base_img_dir: str | None = get_base_image_path(self.DATA_SOURCE_FOLDER_NAME)

        if base_img_dir is None:
            pytest.fail("Base image directory is None")

        img_h, img_w, _ = imread(base_img_dir).shape

        cube_img_w_ratio: float = cube_w / img_w
        cube_img_h_ratio: float = cube_h / img_h
        cube_img_selection_area_ratio: float = cube_img_w_ratio * cube_img_h_ratio

        selection_rgb_w: int = abs(RGB_POINT_2[0] - RGB_POINT_1[0]) + 1
        selection_rgb_h: int = abs(RGB_POINT_2[1] - RGB_POINT_1[1]) + 1
        selection_rgb_area_size: int = selection_rgb_w * selection_rgb_h

        expected_size: int = round(selection_rgb_area_size * cube_img_selection_area_ratio)

        # execute
        selection_data: np.ndarray | None = get_selected_data_cube(
            self.DATA_SOURCE_FOLDER_NAME, RGB_POINT_1, RGB_POINT_2
        )

        if selection_data is None:
            pytest.fail("An error occured while extracting data cube selected region.")

        # verify
        actual_size: int = selection_data.shape[1]

        # Calculate a percentage-based tolerance, because of rounding
        tolerance_percentage: float = 0.02  # 2% tolerance
        tolerance: float = expected_size * tolerance_percentage

        assert abs(actual_size - expected_size) <= tolerance
