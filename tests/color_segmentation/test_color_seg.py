import sys
from os.path import join
from pathlib import Path
import numpy as np

sys.path.append('.')

from xrf_explorer.server.color_seg import get_image, get_clusters_using_k_means, merge_similar_colors

RESOURCES_PATH: Path = Path('tests', 'resources')


class TestColorSegmentation:
    BW_IMAGE_PATH: str = join(RESOURCES_PATH, Path('color_segmentation', 'black_and_white_image.png'))

    def test_get_clusters_using_k_means(self):
        # Set-up
        small_image: str = get_image(self.BW_IMAGE_PATH)
        expected_result = np.array([
            [0, 0, 0],
            [255, 255, 255]
        ])
        expected_result2 = np.array([
            [255, 255, 255],
            [0, 0, 0]
        ])

        # Execute
        useless_labels, result = get_clusters_using_k_means(small_image)
        print(result)
        result = merge_similar_colors(result, 200)

        print(result)
        length = len(result)

        # Verify
        assert len(expected_result) == length
        assert np.array_equal(result, expected_result) or np.array_equal(result, expected_result2)
