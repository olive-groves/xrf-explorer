import logging

from os.path import join

import numpy as np

from xrf_explorer.server.file_system import set_config
from xrf_explorer.server.process.color_segmentation.color_seg import (
    get_image, get_clusters_using_k_means, merge_similar_colors,
    get_elemental_clusters_using_k_means, combine_bitmasks,
    image_to_lab, image_to_rgb, lab_to_rgb, rgb_to_lab
)

RESOURCES_PATH: str = join('tests', 'resources')


class TestColorSegmentation:
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, 'configs', 'color-segmentation.yml')

    DATA_SOURCE = "data_source"
    IMAGE_NAME = "RGB"

    PATH_DATA_SOURCE: str = join(RESOURCES_PATH, 'color_segmentation', DATA_SOURCE)

    BW_IMAGE_PATH: str = join(RESOURCES_PATH, 'color_segmentation', 'black_and_white_image.png')
    TEST_IMAGE_PATH: str = join(PATH_DATA_SOURCE, 'test_image_cs.png')
    DATA_CUBE_PATH: str = join(PATH_DATA_SOURCE, 'test_cube.dms')
    REG_TEST_IMAGE_PATH: str = join(PATH_DATA_SOURCE, 'registered_test_image.png')

    def test_get_clusters_using_k_means_colors(self, caplog):
        caplog.set_level(logging.INFO)
        set_config(self.CUSTOM_CONFIG_PATH)

        # Set-up
        result: np.ndarray
        num_attempts: int = 10
        k: int = 2

        # Execute
        result, _ = get_clusters_using_k_means(self.DATA_SOURCE, self.IMAGE_NAME, k, num_attempts)
        print(result)
        # Verify
        # The image has 2 colors
        assert len(result) == 2
        assert np.sum(np.all(result == [0, 0, 0], axis=1)) == 1
        assert np.sum(np.all(result == [189, 189, 189], axis=1)) == 1

        # Verify log message
        assert "Initial color clusters extracted successfully." in caplog.text

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

    def test_invalid_path_to_image(self, caplog):
        # Set-up
        fake_path: str = join(RESOURCES_PATH, "fake")

        # Execute
        result: np.ndarray = get_image(fake_path)

        # Verify
        assert np.array_equal(result, np.empty(0))

        # Verify log message
        assert f"The path '{fake_path}' is not a valid file path" in caplog.text

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

    def test_get_elem_clusters_using_k_means(self):
        set_config(self.CUSTOM_CONFIG_PATH)

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
        elem_threshold: float = 0.1
        num_attemps: int = 10
        k: int = 2

        # Execute
        clusters_per_elem: list[np.ndarray] = []
        bitmasks_per_elem: list[np.ndarray] = []

        for i in range(3):
            bitmask: np.ndarray
            clusters: np.ndarray
            clusters, bitmask = get_elemental_clusters_using_k_means(
                self.DATA_SOURCE, self.IMAGE_NAME, i, elem_threshold, k, num_attemps
            )
            clusters_per_elem.append(clusters)
            bitmasks_per_elem.append(bitmask)

        # Verify
        assert np.array_equal(clusters_per_elem[0], expected_result0)
        assert np.array_equal(clusters_per_elem[1], expected_result1)
        assert np.array_equal(clusters_per_elem[2], expected_result2)

    def test_image_to_rgb_and_lab(self):
        # Set-up
        original_image: np.ndarray = get_image(self.BW_IMAGE_PATH)

        # Execute
        image = image_to_lab(original_image)
        image = image_to_rgb(image)

        # Verify
        assert np.array_equal(original_image, original_image)

    def test_rgb_to_lab(self):
        # Set-up
        color: np.ndarray = np.array([10, 160, 230]).astype(np.uint8)

        # Execute
        new_col = rgb_to_lab(color)
        new_col = lab_to_rgb(new_col).astype(np.uint8)

        # Verify
        assert np.array_equal(new_col, color)
