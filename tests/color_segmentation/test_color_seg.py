import logging
import sys
from os.path import join
from pathlib import Path

import numpy as np

sys.path.append('.')

from xrf_explorer.server.color_seg import (
    get_image, get_clusters_using_k_means, merge_similar_colors,
    get_elemental_clusters_using_k_means, get_pixels_in_clusters,
    get_pixels_in_clusters_element, combine_bitmasks, get_small_image)

RESOURCES_PATH: Path = Path('tests', 'resources')


class TestColorSegmentation:
    BW_IMAGE_PATH: str = join(RESOURCES_PATH, Path('color_segmentation', 'black_and_white_image.png'))
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, Path('configs', 'elemental-data.yml'))
    DATA_CUBE_DMS: str = 'test.dms'

    def test_get_clusters_using_k_means(self, caplog):
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
        useless_labels, result = get_clusters_using_k_means(small_image)

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

        # Execute
        useless_labels, result = get_clusters_using_k_means(small_image)
        result: np.array = merge_similar_colors(result)

        # Verify
        assert len(expected_result) == len(result)
        assert np.array_equal(result, expected_result)

        # Verify log message
        assert "Similar clusters merged successfully." in caplog.text

    def test_get_pixels_in_clusters(self, caplog):
        caplog.set_level(logging.INFO)

        # Set-up
        image: np.array = get_image(self.BW_IMAGE_PATH)
        clusters: np.array = np.array([
            [255, 255, 255],
            [0, 0, 0]
        ])
        white_cluster: np.array = np.zeros((100, 100), dtype=int)
        white_cluster[:, 50:] = 255
        black_cluster: np.array = np.zeros((100, 100), dtype=int)
        black_cluster[:, :50] = 255

        # Execute
        bitmask: np.array = get_pixels_in_clusters(image, clusters)

        # Verify
        assert np.array_equal(white_cluster, bitmask[0])
        assert np.array_equal(black_cluster, bitmask[1])

        # Verify log message
        assert "Successfully computed bitmasks." in caplog.text

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
        bitmask1 = np.array([[0, 255], [255, 0]], dtype=np.uint8)
        bitmask2 = np.array([[255, 0], [0, 255]], dtype=np.uint8)
        bitmask3 = np.array([[0, 0], [255, 255]], dtype=np.uint8)
        bitmask4 = np.array([[255, 255], [255, 255]], dtype=np.uint8)
        bitmasks = [bitmask1, bitmask2, bitmask3, bitmask1,
                    bitmask1, bitmask1, bitmask1, bitmask1,
                    bitmask1, bitmask2, bitmask3, bitmask2,
                    bitmask1, bitmask1, bitmask1, bitmask1,
                    bitmask4, bitmask2, bitmask3, bitmask1]
        expected_result = [
            [[0b00000010, 0b00001010, 0b00000011, 0b00000000], [0b11111001, 0b11110001, 0b00001001, 0b00000000]],
            [[0b11111101, 0b11110101, 0b00001101, 0b00000000], [0b00000110, 0b00001110, 0b00000111, 0b00000000]]
        ]

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
        img_dim = 100
        elem_threshold = 0.1

        # Execute
        clusters_per_elem = get_elemental_clusters_using_k_means(small_image, self.DATA_CUBE_DMS, self.CUSTOM_CONFIG_PATH, elem_threshold, img_dim)
        for i in range(len(clusters_per_elem)):
            clusters_per_elem[i] = merge_similar_colors(clusters_per_elem[i])

        # Verify
        assert np.array_equal(clusters_per_elem[0], expected_result0)
        assert np.array_equal(clusters_per_elem[1], expected_result1)

    def test_get_pixels_in_clusters_element(self):
        # Set-up
        small_image: str = get_image(self.BW_IMAGE_PATH)
        img_dim = 100
        elem_threshold = 0.1

        # Execute
        clusters_per_elem = get_elemental_clusters_using_k_means(small_image, self.DATA_CUBE_DMS, self.CUSTOM_CONFIG_PATH, elem_threshold, img_dim)
        for i in range(len(clusters_per_elem)):
            clusters_per_elem[i] = merge_similar_colors(clusters_per_elem[i])

        elem_bitmasks = get_pixels_in_clusters_element(small_image, clusters_per_elem, self.DATA_CUBE_DMS, self.CUSTOM_CONFIG_PATH, elem_threshold)

        white_cluster = np.zeros((100, 100), dtype=int)
        white_cluster[:, 50:] = 1
        black_cluster = np.zeros((100, 100), dtype=int)
        black_cluster[:, :50] = 1

        # Verify
        assert np.array_equal(elem_bitmasks[1][0], black_cluster)
        assert np.array_equal(elem_bitmasks[1][1], white_cluster)
        assert np.array_equal(elem_bitmasks[0], np.array([]))
