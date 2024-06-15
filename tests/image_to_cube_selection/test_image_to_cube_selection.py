import numpy as np

import sys
import pytest
from cv2 import imread, fillPoly

from os.path import join

sys.path.append(".")

from xrf_explorer.server.image_to_cube_selection.image_to_cube_selection import perspective_transform_coord

from xrf_explorer.server.file_system.file_access import (
    get_elemental_cube_path,
    get_base_image_path,
)
from xrf_explorer.server.file_system.elemental_cube import get_elemental_data_cube
from xrf_explorer.server.image_to_cube_selection import (
    get_selection,
    get_scaled_cube_coordinates,
    deregister_coord,
    SelectionType
)
from xrf_explorer.server.file_system.config_handler import set_config

RESOURCES_PATH: str = join("tests", "resources")


class TestImageToCubeSelection:
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, "configs", "image_to_cube_selection.yml")
    DATA_SOURCE_FOLDER_NAME: str = "Data_source"
    SAMPLE_BASE_IMAGE_PATH: str = join(RESOURCES_PATH, "image_to_cube_selection", "rgb.tif")
    SAMPLE_CUBE_IMG_PATH: str = join(RESOURCES_PATH, "image_to_cube_selection", "cube.tif")
    SAMPLE_CUBE_RECIPE_PATH: str = join(RESOURCES_PATH, "image_to_cube_selection", "recipe_cube.csv")

    @pytest.fixture(autouse=True)
    def setup_environment(self):
        set_config(self.CUSTOM_CONFIG_PATH)
        yield

    def test_get_selected_data_cube_dir_not_found(self, caplog):
        # setup
        rgb_points: list[tuple[int, int]] = [
            (0, 0),
            (1, 1)
        ]

        data_source_folder_name: str = "made_up_name"
        expected_output: str = f"Data source directory {data_source_folder_name} does not exist."

        # execute
        result: np.ndarray | None = get_selection(
            data_source_folder_name, rgb_points, SelectionType.Rectangle
        )

        assert result is None
        assert expected_output in caplog.text

    def test_get_selected_data_cube_dir_found(self):
        # setup
        rgb_points: list[tuple[int, int]] = [
            (0, 0),
            (1, 1)
        ]

        # execute
        result: np.ndarray | None = get_selection(
            self.DATA_SOURCE_FOLDER_NAME, rgb_points, SelectionType.Rectangle
        )

        assert result is not None

    def test_get_cube_coordinates(self):
        # setup
        rgb_points: list[tuple[int, int]] = [
            (2, 6),
            (4, 10)
        ]

        data_cube_point_1_expected: tuple[int, int] = (1, 3)
        data_cube_point_2_expected: tuple[int, int] = (2, 5)

        base_image_height: int = 10
        base_image_width: int = 10
        cube_image_height: int = 5
        cube_image_width: int = 5

        # execute
        data_cube_output_1_actual: tuple[int, int]
        data_cube_output_2_actual: tuple[int, int]
        data_cube_output_1_actual, data_cube_output_2_actual = get_scaled_cube_coordinates(
            rgb_points,
            base_image_width,
            base_image_height,
            cube_image_width,
            cube_image_height,
        )

        # verify
        assert data_cube_output_1_actual == data_cube_point_1_expected
        assert data_cube_output_2_actual == data_cube_point_2_expected

    def test_get_selected_data_cube_output_size(self):
        # setup
        rgb_points: list[tuple[int, int]] = [
            (0, 0),
            (345, 678)
        ]

        cube_dir: str | None = get_elemental_cube_path(self.DATA_SOURCE_FOLDER_NAME)

        if cube_dir is None:
            pytest.fail("Cube directory is None.")

        cube: np.ndarray = get_elemental_data_cube(cube_dir)
        _, cube_h, cube_w = cube.shape

        base_img_dir: str | None = get_base_image_path(self.DATA_SOURCE_FOLDER_NAME)

        if base_img_dir is None:
            pytest.fail("Base image directory is None")
        
        img_h: int
        img_w: int
        img_h, img_w, _ = imread(base_img_dir).shape

        cube_img_w_ratio: float = cube_w / img_w
        cube_img_h_ratio: float = cube_h / img_h
        cube_img_selection_area_ratio: float = cube_img_w_ratio * cube_img_h_ratio

        selection_rgb_w: int = abs(rgb_points[1][0] - rgb_points[0][0]) + 1
        selection_rgb_h: int = abs(rgb_points[1][1] - rgb_points[0][1]) + 1
        selection_rgb_area_size: int = selection_rgb_w * selection_rgb_h

        expected_size: int = round(selection_rgb_area_size * cube_img_selection_area_ratio)

        # execute
        selection_data: np.ndarray | None = get_selection(
            self.DATA_SOURCE_FOLDER_NAME, rgb_points, SelectionType.Rectangle
        )

        if selection_data is None:
            pytest.fail("An error occured while extracting data cube selected region.")

        # verify
        actual_size: int = selection_data.shape[1]

        # Calculate a percentage-based tolerance, because of rounding
        tolerance_percentage: float = 0.02  # 2% tolerance
        tolerance: float = expected_size * tolerance_percentage

        assert abs(actual_size - expected_size) <= tolerance

    def test_selections_equivalent(self):
        # setup
        top_left: tuple[int, int] = (0, 0)
        top_right: tuple[int, int] = (345, 0)
        bottom_left: tuple[int, int] = (0, 678)
        bottom_right: tuple[int, int] = (345, 678)

        coords_rect: list[tuple[int, int]] = [top_left, bottom_right]
        coords_lasso: list[tuple[int, int]] = [top_left, top_right, bottom_right, bottom_left]

        # execute
        selection_data_rect: np.ndarray | None = get_selection(
            self.DATA_SOURCE_FOLDER_NAME, coords_rect, SelectionType.Rectangle
        )
        selection_data_lasso: np.ndarray | None = get_selection(
            self.DATA_SOURCE_FOLDER_NAME, coords_lasso, SelectionType.Lasso
        )

        # verify
        assert selection_data_rect is not None
        assert selection_data_lasso is not None
        assert np.array_equal(selection_data_rect, selection_data_lasso)

    def test_negative_coordinates(self):
        # setup
        img_w, img_h, _ = imread(self.SAMPLE_BASE_IMAGE_PATH).shape

        top_left: tuple[int, int] = (0, 0)
        top_right: tuple[int, int] = (img_w - 1, 0)
        bottom_left: tuple[int, int] = (0, img_h - 1)
        bottom_right: tuple[int, int] = (img_w - 1, img_h - 1)

        top_left_outside: tuple[int, int] = (-100, 0)
        bottom_left_outside: tuple[int, int] = (0, img_h + 10)

        coords_rect: list[tuple[int, int]] = [top_left, bottom_right]
        coords_lasso: list[tuple[int, int]] = [top_left, top_right, bottom_right, bottom_left]
        coords_rect_outside: list[tuple[int, int]] = [top_left_outside, bottom_right]
        coords_lasso_outside: list[tuple[int, int]] = [top_left_outside, top_right, bottom_right, bottom_left_outside]

        # execute
        selection_data_rect: np.ndarray | None = get_selection(
            self.DATA_SOURCE_FOLDER_NAME, coords_rect, SelectionType.Rectangle
        )
        selection_data_lasso: np.ndarray | None = get_selection(
            self.DATA_SOURCE_FOLDER_NAME, coords_lasso, SelectionType.Lasso
        )
        selection_data_rect_outside: np.ndarray | None = get_selection(
            self.DATA_SOURCE_FOLDER_NAME, coords_rect_outside, SelectionType.Rectangle
        )
        selection_data_lasso_outside: np.ndarray | None = get_selection(
            self.DATA_SOURCE_FOLDER_NAME, coords_lasso_outside, SelectionType.Lasso
        )

        # verify
        assert selection_data_rect is not None
        assert selection_data_lasso is not None
        assert selection_data_rect_outside is not None
        assert selection_data_lasso_outside is not None

        assert np.array_equal(selection_data_rect, selection_data_lasso)
        assert np.array_equal(selection_data_rect_outside, selection_data_lasso_outside)
        assert np.array_equal(selection_data_rect_outside, selection_data_rect)


    def test_ribbon_selection(self):
        # setup
        img_w, img_h, _ = imread(self.SAMPLE_BASE_IMAGE_PATH).shape

        top_left: tuple[int, int] = (0, 0)
        top_right: tuple[int, int] = (img_w - 1, 0)
        bottom_left: tuple[int, int] = (0, img_h - 1)
        bottom_right: tuple[int, int] = (img_w - 1, img_h - 1)

        coords_rect: list[tuple[int, int]] = [top_left, bottom_right]
        coords_lasso: list[tuple[int, int]] = [top_left, bottom_right, top_right, bottom_left]

        tolerance_percentage: float = 0.01  # 1% tolerance

        # execute
        selection_data_rect: np.ndarray | None = get_selection(
            self.DATA_SOURCE_FOLDER_NAME, coords_rect, SelectionType.Rectangle
        )
        selection_data_lasso: np.ndarray | None = get_selection(
            self.DATA_SOURCE_FOLDER_NAME, coords_lasso, SelectionType.Lasso
        )
        tolerance: float = selection_data_rect.shape[1] * tolerance_percentage

        # verify
        assert selection_data_rect is not None
        assert selection_data_lasso is not None

        # ribbon selection must be about half of the rect selection
        assert abs(selection_data_rect.shape[1] - selection_data_lasso.shape[1] * 2) <= tolerance
        

    # Return true if cube_coord_expected is within tolerance_pixels from the cube coordinate calculated by
    # deregister_coord.
    def is_deregistration_correct(
        self,
        base_img_coord: tuple[int, int],
        cube_coord_expected: tuple[int, int],
        tolerance_pixels: int,
    ) -> bool:
        base_img: np.ndarray = imread(self.SAMPLE_BASE_IMAGE_PATH)
        cube_img: np.ndarray = imread(self.SAMPLE_CUBE_IMG_PATH)

        base_h: int
        base_w: int
        cube_h: int
        cube_w: int
        base_h, base_w, _ = base_img.shape
        cube_h, cube_w, _ = cube_img.shape

        args = (self.SAMPLE_CUBE_RECIPE_PATH, base_h, base_w, cube_h, cube_w)
        cube_coord_actual = deregister_coord(base_img_coord, *args)

        euclidean_dist: int = (
        (cube_coord_expected[0] - cube_coord_actual[0]) ** 2 +
        (cube_coord_expected[1] - cube_coord_actual[1]) ** 2
        )

        return euclidean_dist <= tolerance_pixels

    def test_deregister_coord(self):
        BASE_IMG_COORD_1: tuple[int, int] = (2046, 2691)
        CUBE_COORD_EXPECTED_1: tuple[int, int] = (438, 522)

        BASE_IMG_COORD_2: tuple[int, int] = (2531, 1773)
        CUBE_COORD_EXPECTED_2: tuple[int, int] = (540, 327)

        BASE_IMG_COORD_3: tuple[int, int] = (1020, 1933)
        CUBE_COORD_EXPECTED_3: tuple[int, int] = (218, 360)

        TOLERANCE_PIXELS: int = 20

        assert self.is_deregistration_correct(BASE_IMG_COORD_1, CUBE_COORD_EXPECTED_1, TOLERANCE_PIXELS)
        assert self.is_deregistration_correct(BASE_IMG_COORD_2, CUBE_COORD_EXPECTED_2, TOLERANCE_PIXELS)
        assert self.is_deregistration_correct(BASE_IMG_COORD_3, CUBE_COORD_EXPECTED_3, TOLERANCE_PIXELS)
