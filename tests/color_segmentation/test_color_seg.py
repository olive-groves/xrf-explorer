import sys
from os.path import join
from pathlib import Path
import numpy as np

sys.path.append('.')

from xrf_explorer.server.color_seg import get_image, get_clusters_using_k_means, merge_similar_colors, \
    get_elemental_clusters_using_k_means, get_pixels_in_clusters, get_pixels_in_clusters_element, combine_bitmasks

RESOURCES_PATH: Path = Path('tests', 'resources')


class TestColorSegmentation:
    BW_IMAGE_PATH: str = join(RESOURCES_PATH, Path('color_segmentation', 'black_and_white_image.png'))
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, Path('configs', 'elemental-data.yml'))
    DATA_CUBE_DMS: str = 'test.dms'

    def test_get_clusters_using_k_means(self):
        # Set-up
        small_image: str = get_image(self.BW_IMAGE_PATH)

        # The default number of clusters is 30, which is what we use here. The image only has 2 colors, hence 15
        # clusters for each color.
        expected_result = np.array([
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

    def test_merge_similar_colors(self):
        # Set-up
        small_image: str = get_image(self.BW_IMAGE_PATH)

        # Expected result is a list of two clusters, one for each color of the test image.
        expected_result = np.array([
            [0, 0, 0],
            [255, 255, 255]
        ])

        # Execute
        useless_labels, result = get_clusters_using_k_means(small_image)
        result = merge_similar_colors(result)

        # Verify
        assert len(expected_result) == len(result)
        assert np.array_equal(result, expected_result)

    def test_get_pixels_in_clusters(self):
        # Set-up
        image: str = get_image(self.BW_IMAGE_PATH)
        clusters = np.array([
            [255, 255, 255],
            [0, 0, 0]
        ])
        white_cluster = np.zeros((100, 100), dtype=int)
        white_cluster[:, 50:] = 255
        black_cluster = np.zeros((100, 100), dtype=int)
        black_cluster[:, :50] = 255

        # Execute
        bitmask = get_pixels_in_clusters(image, clusters)

        # Verify
        assert np.array_equal(white_cluster, bitmask[0])
        assert np.array_equal(black_cluster, bitmask[1])

    def test_invalid_path_to_image(self, caplog):
        # Set-up
        fake_path: str = join(RESOURCES_PATH, Path("fake"))

        # Execute
        result = get_image(fake_path)

        # Verify
        assert result is None

        # Verify log message
        assert "The path 'tests/resources/fake' is not a valid file path." in caplog.text

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
            [[0b00000010, 0b00001010, 0b00000011], [0b11111001, 0b11110001, 0b00001001]],
            [[0b11111101, 0b11110101, 0b00001101], [0b00000110, 0b00001110, 0b00000111]]
        ]

        # Execute
        result = combine_bitmasks(bitmasks)

        # Verify
        assert len(expected_result) == len(result)
        assert np.array_equal(result, expected_result)

    def test_get_elem_clusters_using_k_means(self):
        # Set-up
        small_image: str = get_image(self.BW_IMAGE_PATH)

        # Execute
        clusters_per_elem = get_elemental_clusters_using_k_means(small_image, self.DATA_CUBE_DMS, self.CUSTOM_CONFIG_PATH)
        for i in range(len(clusters_per_elem)):
            clusters_per_elem[i] = merge_similar_colors(clusters_per_elem[i])

        # Verify
        # First element is not present so no clusters
        assert len(clusters_per_elem[0]) == 0
        # Second element gets two clusters
        assert len(clusters_per_elem[1]) == 2

    def test_get_pixels_in_clusters_element(self):
        # Setup
        small_image: str = get_image(self.BW_IMAGE_PATH)
        clusters_per_elem = get_elemental_clusters_using_k_means(small_image, self.DATA_CUBE_DMS, self.CUSTOM_CONFIG_PATH)
        for i in range(len(clusters_per_elem)):
            clusters_per_elem[i] = merge_similar_colors(clusters_per_elem[i])

        # Execute
        elem_bitmasks = get_pixels_in_clusters_element(small_image, clusters_per_elem, self.DATA_CUBE_DMS, self.CUSTOM_CONFIG_PATH)
        print(elem_bitmasks)

        # Verify

        assert False
