import logging

from os.path import join

import numpy as np
import cv2

from xrf_explorer.server.file_system import set_config
from xrf_explorer.server.color_segmentation.color_seg import (
    get_clusters_using_k_means, merge_similar_colors,
    get_elemental_clusters_using_k_means, combine_bitmasks,
    image_to_lab, image_to_rgb, lab_to_rgb, rgb_to_lab,
    convert_to_hex, save_bitmask_as_png
)

from xrf_explorer.server.color_segmentation.helper import get_path_to_cs_folder

RESOURCES_PATH: str = join('tests', 'resources')

def empty_array(array: list[np.ndarray]):
    empty: np.ndarray = np.empty(0)
    for i in range(0, len(array)):
        if not np.array_equal(empty, array[i]):
            return False
    return True


class TestColorSegmentation:
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, 'configs', 'color-segmentation.yml')
    WRONG_CONFIG_PATH: str = join(RESOURCES_PATH, 'configs', 'random.yml')

    DATA_SOURCE = "data_source"
    IMAGE_NAME = "RGB"

    PATH_DATA_SOURCE: str = join(RESOURCES_PATH, 'color_segmentation', DATA_SOURCE)

    BW_IMAGE_PATH: str = join(RESOURCES_PATH, 'color_segmentation', 'black_and_white_image.png')
    BITMASK_PATH: str = join(PATH_DATA_SOURCE, 'bitmask.png')
    TEST_IMAGE_PATH: str = join(PATH_DATA_SOURCE, 'test_image_cs.png')
    DATA_CUBE_PATH: str = join(PATH_DATA_SOURCE, 'test_cube.dms')
    REG_TEST_IMAGE_PATH: str = join(PATH_DATA_SOURCE, 'registered_test_image.png')

    elem_threshold: float = 0.1
    num_attempts: int = 10
    k: int = 2

    def test_get_clusters_using_k_means_colors(self, caplog):
        caplog.set_level(logging.INFO)
        set_config(self.CUSTOM_CONFIG_PATH)

        # Set-up
        result: np.ndarray

        # Execute
        result, _ = get_clusters_using_k_means(self.DATA_SOURCE, self.IMAGE_NAME, self.k, self.num_attempts)
        # Verify
        # The image has 2 colors
        assert len(result) == 2
        assert np.sum(np.all(result == [0, 0, 0], axis=1)) == 1
        assert np.sum(np.all(result == [189, 189, 189], axis=1)) == 1

        # Verify log message
        assert "Initial color clusters extracted successfully." in caplog.text

    def test_get_clusters_using_k_means_colors_register_fail(self, caplog):
        caplog.set_level(logging.INFO)
        set_config(self.CUSTOM_CONFIG_PATH)

        # Set-up
        result: np.ndarray
        empty: np.ndarray = np.empty(0)

        # Execute
        result, _ = get_clusters_using_k_means("", self.IMAGE_NAME, self.k, self.num_attempts)

        # Verify
        assert np.array_equal(empty, result)

        # Verify log message
        assert "Image could not be registered to data cube" in caplog.text

    def test_merge_similar_colors(self, caplog):
        caplog.set_level(logging.INFO)

        # Set-up
        # One white cluster, two black cluster
        white_cluster: np.ndarray = np.zeros((3, 3), dtype=bool)
        white_cluster[:, 0] = True
        black_cluster: np.ndarray = np.zeros((3, 3), dtype=bool)
        black_cluster[:, 1] = True
        black_cluster2: np.ndarray = np.zeros((3, 3), dtype=bool)
        black_cluster2[:, 2] = True
        black_cluster_merged: np.ndarray = np.zeros((3, 3), dtype=bool)
        black_cluster_merged[:, 1:3] = True
        colors: np.ndarray = np.array([[255, 255, 255], [0, 0, 0], [0, 0, 0]])
        bitmask: np.ndarray = np.array([white_cluster, black_cluster, black_cluster2])

        # Execute
        colors, bitmask = merge_similar_colors(colors, bitmask)

        # Verify
        assert len(colors) == 2
        assert np.sum(np.all(colors == [0, 0, 0], axis=1)) == 1
        assert np.sum(np.all(colors == [255, 255, 255], axis=1)) == 1
        assert len(colors) == len(bitmask)
        assert np.array_equal(white_cluster, bitmask[0])
        assert np.array_equal(black_cluster_merged, bitmask[1])

        # Verify log message
        assert "Similar clusters merged successfully." in caplog.text

    def test_merge_similar_colors_empty(self, caplog):
        caplog.set_level(logging.INFO)

        # Set-up
        colors: np.ndarray = np.empty(0)
        bitmask: np.ndarray = np.empty(0)
        empty: np.ndarray = np.empty(0)

        # Execute
        colors, bitmask = merge_similar_colors(colors, bitmask)

        # Verify
        assert np.array_equal(colors, empty)
        assert np.array_equal(bitmask, empty)

        # Verify log message
        assert "Cluster or bitmask array length is zero" in caplog.text

    def test_combined_bitmasks(self):
        # Set-up
        bitmask1: np.ndarray = np.array([[False, False, True], [True, False, False]], dtype=bool)
        bitmask2: np.ndarray = np.array([[True, False, False], [False, False, True]], dtype=bool)
        bitmask3: np.ndarray = np.array([[False, True, False], [False, False, False]], dtype=bool)
        bitmasks: list[np.ndarray] = [bitmask1, bitmask2, bitmask3]
        expected_entries: np.ndarray = np.array([[2, 3, 1], [1, 0, 2]], dtype=np.uint8)
        expected_result: np.ndarray = np.zeros((2, 3, 3), dtype=np.uint8)
        expected_result[:, :, 1] = expected_entries

        # Execute
        result: np.ndarray = combine_bitmasks(bitmasks)

        # Verify
        assert len(expected_result) == len(result)
        assert np.array_equal(result, expected_result)

    def test_combined_empty_bitmasks(self):
        # Set-up
        bitmasks: list[np.ndarray] = []
        empty: np.ndarray = np.empty(0)

        # Execute
        result: np.ndarray = combine_bitmasks(bitmasks)

        # Verify
        assert np.array_equal(result, empty)

    def setup_get_elemental_clusters(self, missing_param: str):
        # Set-up
        set_config(self.CUSTOM_CONFIG_PATH)

        # Execute
        clusters_per_elem: list[np.ndarray] = []
        bitmasks_per_elem: list[list[np.ndarray]] = []

        for i in range(3):
            bitmask: list[np.ndarray]
            clusters: np.ndarray
            if missing_param == "datasource":
                clusters, bitmask = get_elemental_clusters_using_k_means(
                    "", self.IMAGE_NAME, i, self.elem_threshold, self.k, self.num_attempts
                )
            elif missing_param == "image":
                clusters, bitmask = get_elemental_clusters_using_k_means(
                    self.DATA_SOURCE, "", i, self.elem_threshold, self.k, self.num_attempts
                )
            else:
                clusters, bitmask = get_elemental_clusters_using_k_means(
                    self.DATA_SOURCE, self.IMAGE_NAME, i, self.elem_threshold, self.k, self.num_attempts
                )
            clusters_per_elem.append(clusters)
            bitmasks_per_elem.append(bitmask)
        return clusters_per_elem, bitmasks_per_elem

    def test_get_elem_clusters_using_k_means(self):
        # Set-up
        expected_result0: np.ndarray = np.array([
            [0, 0, 0],
            [211, 211, 211]
        ])
        expected_result1: np.ndarray = np.array([
            [0, 0, 0],
            [169, 169, 169]
        ])
        expected_result2: np.ndarray = np.array([
            [0, 0, 0],
            [211, 211, 211]
        ])

        # Execute
        clusters_per_elem: list[np.ndarray] = []
        bitmasks_per_elem: list[list[np.ndarray]] = []
        clusters_per_elem, bitmasks_per_elem = self.setup_get_elemental_clusters("")

        # Verify
        assert np.array_equal(clusters_per_elem[0], expected_result0)
        assert np.array_equal(clusters_per_elem[1], expected_result1)
        assert np.array_equal(clusters_per_elem[2], expected_result2)

    def test_get_elem_clusters_using_k_means_elemental_not_found(self, caplog):
        # Execute
        clusters_per_elem: list[np.ndarray]
        bitmasks_per_elem: list[list[np.ndarray]]
        clusters_per_elem, bitmasks_per_elem = self.setup_get_elemental_clusters("datasource")

        # Verify
        assert empty_array(clusters_per_elem)
        assert empty_array(bitmasks_per_elem)

        # Verify log message
        assert "Elemental data cube not found" in caplog.text

    def test_get_elem_clusters_using_k_means_register_fail(self, caplog):
        # Execute
        clusters_per_elem: list[np.ndarray]
        bitmasks_per_elem: list[list[np.ndarray]]
        clusters_per_elem, bitmasks_per_elem = self.setup_get_elemental_clusters("image")

        # Verify
        assert empty_array(clusters_per_elem)
        assert empty_array(bitmasks_per_elem)

        # Verify log message
        assert "Image could not be registered to data cube" in caplog.text

    def test_get_elem_clusters_using_k_means_empty_mask(self):
        set_config(self.CUSTOM_CONFIG_PATH)

        # Set-up
        empty: np.ndarray = np.empty([0])
        high_elem_threshold: float = 1000

        # Execute
        bitmask: list[np.ndarray]
        clusters: np.ndarray
        clusters, bitmask = get_elemental_clusters_using_k_means(
            self.DATA_SOURCE, self.IMAGE_NAME, 0, high_elem_threshold, self.k, self.num_attempts
        )

        # Verify
        assert np.array_equal(clusters, empty)
        assert np.array_equal(bitmask, empty)

    def test_image_to_rgb_and_lab(self):
        # Set-up
        original_image: np.ndarray = cv2.imread(self.BW_IMAGE_PATH)
        original_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)

        # Execute
        image = image_to_lab(original_image)
        image = image_to_rgb(image)

        # Verify
        assert np.array_equal(original_image, image)

    def test_rgb_to_lab(self):
        # Set-up
        color: np.ndarray = np.array([10, 160, 230]).astype(np.uint8)

        # Execute
        new_col = rgb_to_lab(color)
        new_col = lab_to_rgb(new_col).astype(np.uint8)

        # Verify
        assert np.array_equal(new_col, color)

    def test_convert_to_hex(self):
        # Set-up
        colors: np.ndarray = np.array([[0, 0, 0], [255, 255, 255], [10, 40, 50]])
        expected: np.ndarray = np.array(["#000000", "#ffffff", "#0a2832"])

        # Execute
        result: np.ndarray = convert_to_hex(colors)

        # Verify
        assert np.array_equal(result, expected)

    def test_save_bitmask(self):
        # Set-up
        bitmask: np.ndarray = np.zeros((3, 3), dtype=np.uint8)

        # Execute
        saved: bool = save_bitmask_as_png(bitmask, self.BITMASK_PATH)

        # Verify
        assert saved

    def test_save_bitmask_wrong_path(self, caplog):
        # Set-up
        bitmask: np.ndarray = np.zeros((3, 3), dtype=np.uint8)

        # Execute
        saved: bool = save_bitmask_as_png(bitmask, "")

        # Verify
        assert not saved

        # Verify log message
        assert "An error occurred:" in caplog.text

    def test_save_bitmask_invalid_bitmask(self, caplog):
        # Set-up
        bitmask: np.ndarray = np.empty(0)

        # Execute
        saved: bool = save_bitmask_as_png(bitmask, self.BITMASK_PATH)

        # Verify
        assert not saved

        # Verify log message
        assert "An error occurred:" in caplog.text

    def test_get_path_to_cs_folder(self):
        # Set-up
        expected_path: str = join(self.PATH_DATA_SOURCE, 'generated', 'color_segmentation')

        # Execute
        path: str = get_path_to_cs_folder(self.DATA_SOURCE)

        # Verify
        assert path == expected_path

    def test_get_path_to_cs_folder_wrong_datasource(self, caplog):
        # Set-up
        set_config(self.WRONG_CONFIG_PATH)

        # Execute
        path: str = get_path_to_cs_folder(self.DATA_SOURCE)

        # Verify
        assert not path

        # Verify log message
        assert "Config is empty" in caplog.text
