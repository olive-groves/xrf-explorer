from pathlib import Path
import numpy as np
import pytest

from xrf_explorer.server.file_system.helper import set_config
from xrf_explorer.server.spectra import get_average_global
from xrf_explorer.server.spectra.spectra import get_average_selection


class TestSpectra:
    RESOURCES_PATH = Path('tests', 'resources')
    DATA_SOURCE_FOLDER_NAME: str = "Data_source"
    CUSTOM_CONFIG_PATH: str = str(Path(RESOURCES_PATH, "configs", "spectra.yml")).replace("\\","/")
    TEST_RAW_PATH: str = str(Path(RESOURCES_PATH, "spectra", "data", "Data_source", "data.raw")).replace("\\","/")
    
    @pytest.fixture(autouse=True)
    def setup_environment(self):
        set_config(self.CUSTOM_CONFIG_PATH)
        yield

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
        data: np.ndarray = np.array([[[3, 4], [1, 2], [1, 2]],
                                    [[2, 2], [2, 0], [2, 2]],
                                    [[2, 2], [2, 0], [2, 2]]], dtype=np.uint16)
        
        mask = np.array([[True, False, True],
                         [False, True, True],
                         [True, False, False]])
        
        expected_result: list[float] = [2.0, 2.0]
        
        # execute
        self.numpy_to_raw(data, self.TEST_RAW_PATH)
        result: list[float] = get_average_selection(self.DATA_SOURCE_FOLDER_NAME, mask)

        # verify
        assert result == expected_result
        
    def numpy_to_raw(self, array:np.ndarray, path: str):
        """Writes a numpy array to a raw file.
        
        :param array: The array to write.
        :param path: The path to write the file to.
        """
        array.flatten().tofile(path)