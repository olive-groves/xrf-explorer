from pathlib import Path
import numpy as np
import pytest

from xrf_explorer.server.file_system.helper import set_config
from xrf_explorer.server.file_system.cubes.spectral import numpy_to_raw, mipmap_exists, mipmap_raw_cube, get_raw_data
from xrf_explorer.server.spectra import get_average_global, get_average_selection


class TestSpectra:
    RESOURCES_PATH: Path = Path('tests', 'resources')
    DATA_SOURCE_FOLDER_NAME: str = "spectra_source"
    CUSTOM_CONFIG_PATH: str = str(Path(RESOURCES_PATH, "configs", "spectra.yml")).replace("\\","/")
    TEST_RAW_PATH: str = str(Path(RESOURCES_PATH, "spectra", "data", DATA_SOURCE_FOLDER_NAME, "data.raw")).replace("\\","/")
    TEST_RAW_DATA: np.ndarray = np.array([[[3, 4], [1, 2], [1, 2]],
                                          [[2, 2], [2, 0], [2, 2]],
                                          [[2, 2], [2, 0], [2, 2]]], dtype=np.uint16)
    
    @pytest.fixture(autouse=True)
    def setup_environment(self):
        set_config(self.CUSTOM_CONFIG_PATH)
        numpy_to_raw(self.TEST_RAW_DATA, self.TEST_RAW_PATH)
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
        mask = np.array([[True, False, True],
                         [False, True, True],
                         [True, False, False]])
        
        expected_result: list[float] = [2.0, 2.0]
        
        # execute
        result: list[float] = get_average_selection(self.DATA_SOURCE_FOLDER_NAME, mask)

        # verify
        assert result == expected_result

    def test_get_raw_data(self):
        # execute
        result: np.memmap | np.ndarray = get_raw_data(self.DATA_SOURCE_FOLDER_NAME)

        # verify
        assert np.array_equal(self.TEST_RAW_DATA, result)

    def test_mipmap_not_exist(self):
        # setup
        expected_result: bool = False
        
        # execute
        result: bool = mipmap_exists(self.DATA_SOURCE_FOLDER_NAME, 10)

        # verify
        assert result == expected_result

    def test_mipmap_inexistent_data_source(self):
        # setup
        expected_result: bool = False
        
        # execute
        result: bool = mipmap_exists("inexistent", 10)

        # verify
        assert result == expected_result

    def test_mipmap_low_level(self):
        # setup
        expected_result: bool = True
        
        # execute
        result: bool = mipmap_exists("inexistent", 0)

        # verify
        assert result == expected_result

    def test_mipmap_create(self):
        # setup
        expected_result_exists: bool = True
        
        # execute
        mipmap_raw_cube(self.DATA_SOURCE_FOLDER_NAME, 1)
        result_exists: bool = mipmap_exists(self.DATA_SOURCE_FOLDER_NAME, 1)

        # verify
        assert result_exists == expected_result_exists

    def test_mipmap_data(self):
        # setup
        expected_exists: bool = True
        
        # execute
        exists: bool = mipmap_exists(self.DATA_SOURCE_FOLDER_NAME, 1)
        original_data: np.memmap | np.ndarray = get_raw_data(self.DATA_SOURCE_FOLDER_NAME)
        mipmapped_data: np.memmap | np.ndarray = get_raw_data(self.DATA_SOURCE_FOLDER_NAME, 1)

        # verify
        assert expected_exists == exists
        assert mipmapped_data.shape[0] * 2 - 1 == original_data.shape[0]
        assert mipmapped_data.shape[1] * 2 - 1 == original_data.shape[1]
        assert mipmapped_data.shape[2] == original_data.shape[2]