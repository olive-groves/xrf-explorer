import numpy as np

import sys

from os.path import join
from pathlib import Path

sys.path.append(".")

from xrf_explorer.server.file_system.config_handler import load_yml
from xrf_explorer.server.image_to_cube_selection import (
    get_selected_data_cube,
    get_cube_coordinates,
)

RESOURCES_PATH: str = join("tests", "resources")


class TestImageToCubeSelection:
    CUSTOM_CONFIG_PATH: str = join(
        RESOURCES_PATH, "configs", "image_to_cube_selection.yml"
    )

    def test_get_selected_data_cube_dir_not_found(self, caplog):
        # setup
        first: tuple[int, int] = (0, 0)
        second: tuple[int, int] = (1, 1)

        data_source_folder_name: str = "made_up_name"
        expected_output: str = (
            f"Data source directory {data_source_folder_name} does not exist."
        )

        # execute
        result: np.ndarray | None = get_selected_data_cube(
            data_source_folder_name, first, second, self.CUSTOM_CONFIG_PATH
        )

        # verify
        assert result is None
        assert expected_output in caplog.text

    def test_get_selected_data_cube_dir_found(self):
        # setup
        first: tuple[int, int] = (0, 0)
        second: tuple[int, int] = (1, 1)
        data_source_dir_name: str = "Data_source"

        # result
        result: np.ndarray | None = get_selected_data_cube(
            data_source_dir_name, first, second, self.CUSTOM_CONFIG_PATH
        )

        # verify
        assert result is not None

    def test_get_cube_coordinates(self):
        rgb_point_1 = (2, 6)
        rgb_point_2 = (4, 10)

        data_cube_point_1 = (1, 3)
        data_cube_point_2 = (2, 5)

        base_image_height = 10
        base_image_width = 10
        cube_image_height = 5
        cube_image_width = 5

        data_cube_output_1, data_cube_output_2 = get_cube_coordinates(
            rgb_point_1,
            rgb_point_2,
            base_image_width,
            base_image_height,
            cube_image_width,
            cube_image_height,
        )

        assert data_cube_output_1 == data_cube_point_1
        assert data_cube_output_2 == data_cube_point_2
