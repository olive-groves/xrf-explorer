import sys
from os.path import join
from pathlib import Path
import numpy as np

sys.path.append('.')

from xrf_explorer.server.color_seg import get_image, get_clusters_using_k_means, merge_similar_colors, \
    get_pixels_in_clusters

RESOURCES_PATH: Path = Path('tests', 'resources')


class TestColorSegmentation:
    BW_IMAGE_PATH: str = join(RESOURCES_PATH, Path('color_segmentation', 'black_and_white_image.png'))

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
