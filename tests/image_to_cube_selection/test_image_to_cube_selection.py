from os import RTLD_GLOBAL
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
from cv2 import imread
import pytest

RESOURCES_PATH: str = join("tests", "resources")


class TestImageToCubeSelection:
    CUSTOM_CONFIG_PATH: str = join(
        RESOURCES_PATH, "configs", "image_to_cube_selection.yml"
    )
    DATA_SOURCE_FOLDR_NAME = "Data_source"

    def test_get_selected_data_cube_dir_not_found(self, caplog):
        RGB_POINT_1: tuple[int, int] = (0, 0)
        RGB_POINT_2: tuple[int, int] = (1, 1)

        data_source_folder_name: str = "made_up_name"
        expected_output: str = (
            f"Data source directory {data_source_folder_name} does not exist."
        )

        result: np.ndarray | None = get_selected_data_cube(
            data_source_folder_name, RGB_POINT_1, RGB_POINT_2, self.CUSTOM_CONFIG_PATH
        )

        assert result is None
        assert expected_output in caplog.text

    def test_get_selected_data_cube_dir_found(self):
        RGB_POINT_1: tuple[int, int] = (0, 0)
        RGB_POINT_2: tuple[int, int] = (1, 1)

        result: np.ndarray | None = get_selected_data_cube(
            self.DATA_SOURCE_FOLDR_NAME,
            RGB_POINT_1,
            RGB_POINT_2,
            self.CUSTOM_CONFIG_PATH,
        )

        assert result is not None

    def test_get_cube_coordinates(self):
        RGB_POINT_1 = (2, 6)
        RGB_POINT_2 = (4, 10)

        data_cube_point_1_expected = (1, 3)
        data_cube_point_2_expected = (2, 5)

        base_image_height = 10
        base_image_width = 10
        cube_image_height = 5
        cube_image_width = 5

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

        assert data_cube_output_1_actual == data_cube_point_1_expected
        assert data_cube_output_2_actual == data_cube_point_2_expected

    def test_get_selected_data_cube_output_size(self):
        RGB_POINT_1 = (0, 0)
        RGB_POINT_2 = (345, 678)

        cube_dir = get_elemental_cube_path(
            self.DATA_SOURCE_FOLDR_NAME, self.CUSTOM_CONFIG_PATH
        )

        if cube_dir is None:
            pytest.fail("Cube directory is None.")
            return

        cube = get_elemental_data_cube(cube_dir)
        _, cube_h, cube_w = cube.shape

        base_img_dir = get_base_image_path(
            self.DATA_SOURCE_FOLDR_NAME, self.CUSTOM_CONFIG_PATH
        )

        if base_img_dir is None:
            pytest.fail("Base image directory is None")
            return

        img_h, img_w, _ = imread(base_img_dir).shape

        cube_img_w_ratio = cube_w / img_w
        cube_img_h_ratio = cube_h / img_h
        cube_img_selection_area_ratio = cube_img_w_ratio * cube_img_h_ratio

        selection_rgb_w = abs(RGB_POINT_2[0] - RGB_POINT_1[0]) + 1
        selection_rgb_h = abs(RGB_POINT_2[1] - RGB_POINT_1[1]) + 1
        selection_rgb_area_size = selection_rgb_w * selection_rgb_h

        selection_data = get_selected_data_cube(
            self.DATA_SOURCE_FOLDR_NAME,
            RGB_POINT_1,
            RGB_POINT_2,
            self.CUSTOM_CONFIG_PATH,
        )

        if selection_data is None:
            pytest.fail("An error occured while extracting data cube selected region.")
            return

        actual_size = selection_data.shape[1]
        expected_size = selection_rgb_area_size * cube_img_selection_area_ratio

        if selection_data is None:
            pytest.fail("Selected data is None.")
            return

        # Calculate a percentage-based tolerance, because of rounding
        tolerance_percentage = 0.1  # 10% tolerance
        tolerance = expected_size * tolerance_percentage

        assert abs(actual_size - expected_size) <= tolerance
