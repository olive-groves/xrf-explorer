import logging
import sys
from os.path import join
from pathlib import Path

import numpy as np

sys.path.append('.')

from xrf_explorer.server.color_seg import (
    get_image, get_clusters_using_k_means, merge_similar_colors,
    get_elemental_clusters_using_k_means, combine_bitmasks, get_small_image)

RESOURCES_PATH: Path = Path('tests', 'resources')


class TestColorSegmentation:
    BW_IMAGE_PATH: str = join(RESOURCES_PATH, Path('color_segmentation', 'black_and_white_image.png'))
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, Path('configs', 'elemental-data.yml'))
    DATA_CUBE_DMS: str = 'test.dms'

    def test_get_clusters_using_k_means_colors(self, caplog):
        caplog.set_level(logging.INFO)

        # Set-up
        small_image: np.array = get_image(self.BW_IMAGE_PATH)

        # The default number of clusters is 30, which is what we use here. The image only has 2 colors, hence 15
        # clusters for each color.
        expected_result: np.array = np.array([
            [0, 0, 0], [255, 255, 255], [0, 0, 0], [255, 255, 255], [0, 0, 0], [255, 255, 255],
            [0, 0, 0], [255, 255, 255], [0, 0, 0], [255, 255, 255], [0, 0, 0], [255, 255, 255],
            [0, 0, 0], [255, 255, 255], [0, 0, 0], [255, 255, 255], [0, 0, 0], [255, 255, 255],
            [0, 0, 0], [255, 255, 255], [0, 0, 0], [255, 255, 255], [0, 0, 0], [255, 255, 255],
            [0, 0, 0], [255, 255, 255], [0, 0, 0], [255, 255, 255], [0, 0, 0], [255, 255, 255]
        ])

        # Execute
        _, result, _ = get_clusters_using_k_means(small_image)

        # Verify
        assert len(expected_result) == len(result)
        assert np.array_equal(result, expected_result)

        # Verify log message
        assert "Initial color clusters extracted successfully." in caplog.text

    def test_merge_similar_colors(self, caplog):
        caplog.set_level(logging.INFO)

        # Set-up
        small_image: np.array = get_image(self.BW_IMAGE_PATH)

        # Expected result is a list of two clusters, one for each color of the test image.
        expected_result: np.array = np.array([
            [0, 0, 0],
            [255, 255, 255]
        ])
        white_cluster: np.array = np.zeros((100, 100), dtype=bool)
        white_cluster[:, 50:] = True
        black_cluster: np.array = np.zeros((100, 100), dtype=bool)
        black_cluster[:, :50] = True

        # Execute
        _, colors, bitmask = get_clusters_using_k_means(small_image, 100)
        newColors, newBitmasks = merge_similar_colors(colors, bitmask)

        # Verify
        assert len(expected_result) == len(newColors)
        assert np.array_equal(newColors, expected_result)
        assert len(newColors) == len(newBitmasks)
        assert np.array_equal(white_cluster, newBitmasks[1])
        assert np.array_equal(black_cluster, newBitmasks[0])

        # Verify log message
        assert "Similar clusters merged successfully." in caplog.text

    def test_invalid_path_to_image(self, caplog):
        # Set-up
        fake_path: str = join(RESOURCES_PATH, Path("fake"))

        # Execute
        result: np.array = get_image(fake_path)

        # Verify
        assert np.array_equal(result, np.empty(0))

        # Verify log message
        assert "The path 'tests/resources/fake' is not a valid file path." in caplog.text
        assert f"The path '{fake_path}' is not a valid file path." in caplog.text

    def test_get_small_image(self):
        # Set-up
        big_image: np.array = get_image(self.BW_IMAGE_PATH)

        # Execute
        result: np.array = get_small_image(big_image, 50)

        # verify
        assert np.array_equal(result.shape, (50, 50, 3))  # Check that the shape is correct.
        assert np.array_equal(result[0][0], [0, 0, 0])  # Check that the bottom left pixel is black.
        assert np.array_equal(result[25][25], [255, 255, 255])  # Check proper scaling by checking a white pixel.

    def test_combined_bitmasks(self):
        # Set-up
        bitmask1 = np.array([[False, False, True], [True, False, False]], dtype=bool)
        bitmask2 = np.array([[True, False, False], [False, False, True]], dtype=bool)
        bitmask3 = np.array([[False, True, False], [False, False, False]], dtype=bool)
        bitmasks = [bitmask1, bitmask2, bitmask3]
        expected_entries = [[2, 3, 1], [1, 0, 2]]
        expected_result = np.zeros((2, 3, 3), dtype=np.uint8)
        expected_result[:, :, 0] = expected_entries

        # Execute
        result = combine_bitmasks(bitmasks)

        # Verify
        assert len(expected_result) == len(result)
        assert np.array_equal(result, expected_result)

    def test_get_elem_clusters_using_k_means(self):
        # Set-up
        small_image: str = get_image(self.BW_IMAGE_PATH)
        expected_result0 = np.array([])
        expected_result1 = np.array([
            [0, 0, 0],
            [255, 255, 255]
        ])
        elem_threshold = 0.1

        # Execute
        clusters_per_elem, bitmasks_per_elem = get_elemental_clusters_using_k_means(small_image, self.DATA_CUBE_DMS, self.CUSTOM_CONFIG_PATH, elem_threshold, 100, 100)

        for i in range(len(clusters_per_elem)):
            clusters_per_elem[i], bitmasks_per_elem[i] = merge_similar_colors(clusters_per_elem[i], bitmasks_per_elem[i])


        # Verify
        assert np.array_equal(clusters_per_elem[0], expected_result0)
        assert np.array_equal(clusters_per_elem[1], expected_result1)
