from ntpath import join
from posixpath import abspath
import numpy as np

from xrf_explorer.server.spectra import get_average_global


class TestSpectra:
    RESOURCES_PATH: str = join('tests', 'resources')
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, "configs", "contextual-images.yml")
    TEST_RAW_PATH: str = abspath(join(RESOURCES_PATH, "spectra", "test.raw"))
    INVALID_IMAGE_PATH: str = abspath(join(RESOURCES_PATH, "contextual_images", "painting", "invalid.png"))
    NONEXISTENT_IMAGE_PATH: str = abspath(
        join(RESOURCES_PATH, "contextual_images", "painting", "nonexistent.png"))

    def test_get_average_global(self):
        # setup
        data: np.ndarray = np.array([[[1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4]],
                        [[1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4]]])
        expected_result: list[float] = [1.0, 2.0, 3.0, 4.0]

        # execute
        result: list[float] = get_average_global(data)

        # verify
        assert result == expected_result

    def test_get_average_selection(self):
        # setup
        data = np.array([[[3, 4, 3, 4], [1, 2, 3, 4], [2, 2, 3, 4],
                        [2, 0, 3, 4]]])
        expected_result: list[float] = [2.0, 2.0, 3.0, 4.0]

        # execute
        result: list[float] = get_average_global(data)

        # verify
        assert result == expected_result
        
    def numpy_to_raw(self, array:np.ndarray, path: str):
        """Writes a numpy array to a raw file.
        
        :param array: The array to write.
        :param path: The path to write the file to.
        """
        array.flatten.tofile(path)