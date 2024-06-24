from ntpath import join
from pathlib import Path
import numpy as np
import pytest

from xrf_explorer.server.file_system.cubes.spectral import parse_rpl, mipmap_exists, mipmap_raw_cube, get_raw_data, get_spectra_params, bin_data
from xrf_explorer.server.file_system.helper import set_config
from xrf_explorer.server.file_system.workspace.file_access import get_raw_rpl_paths


class TestSpectral:
    RESOURCES_PATH = Path('tests', 'resources')
    DATA_SOURCE_FOLDER_NAME: str = "Data_source"
    CUSTOM_CONFIG_PATH = str(Path(RESOURCES_PATH, "configs", "spectra.yml")).replace("\\","/")
    TEST_RAW_PATH = str(Path(RESOURCES_PATH, "spectra", "data", "Data_source", "data.raw")).replace("\\","/")
    
    @pytest.fixture(autouse=True)
    def setup_environment(self):
        set_config(self.CUSTOM_CONFIG_PATH)
        yield
    
    def test_parse_rpl(self):
        _, path = get_raw_rpl_paths(self.DATA_SOURCE_FOLDER_NAME)
        info: dict = parse_rpl(path)
        
        expected_info: dict = {
            "key": "value",
            "width": "3",
            "height": "3",
            "depth": "6",
            "offset": "0",
            "data-Length": "2",
            "data-type": "unsigned",
            "byte-order": 	 "little-endian",
            "record-by":  	 "vector",
            "depthbinsize": "1",
            "depth1": "200",
            "depth2": "3000",
            "depthscaleorigin": "-0.956",
            "depthscaleincrement": "0.010002",
            "depthscaleunits": "keV"
            }
        
        assert info == expected_info
        
    def test_parse_rpl_file_not_found(self, caplog):
        
        info: dict = parse_rpl("false_path")
        expected_output: str = "error while reading rpl file: {[Errno 2] No such file or directory: 'false_path'}\n"
        
        assert info == {}
        assert expected_output in caplog.text
        
    def test_get_spectra_params(self):
        params: dict = get_spectra_params(self.DATA_SOURCE_FOLDER_NAME)
        
        assert params["low"] == 1 and params["high"] == 5 and params["binSize"] == 2
        
    def test_get_spectra_params_file_not_found(self):
        
        with pytest.raises(FileNotFoundError) as err:
            params: dict = get_spectra_params("false_name")
            
        assert "" in str(err.value)
    
    def test_bin_data_identity(self):
        # setup
        data: np.ndarray = np.array([[[3, 1, 3, 4, 0, 4], [1, 2, 4, 4, 0, 4], [1, 2, 4, 4, 0, 4]],
                         [[2, 2, 4, 4, 0, 4], [2, 1, 3, 4, 0, 4], [2, 1, 3, 4, 0, 4]],
                         [[2, 1, 3, 4, 0, 4], [2, 0, 2, 4, 0, 4], [2, 2, 4, 4, 0, 4]]], dtype=np.uint16)
        
        self.numpy_to_raw(data, self.TEST_RAW_PATH)
        bin_data(self.DATA_SOURCE_FOLDER_NAME, 0, 2, 1)
        binned_data = get_raw_data(self.DATA_SOURCE_FOLDER_NAME, 0)
        assert data.all() == binned_data.all()
        
    def test_bin_data_(self):
        # setup
        data: np.ndarray = np.array([[[3, 1, 3, 4, 0, 4], [1, 2, 4, 4, 2, 4], [1, 2, 4, 2, 0, 4]],
                                    [[2, 2, 4, 4, 0, 4], [2, 1, 3, 3, 1, 4], [2, 1, 3, 4, 0, 4]],
                                    [[2, 1, 3, 4, 2, 4], [2, 0, 2, 2, 0, 4], [2, 2, 4, 4, 2, 4]]], dtype=np.uint16)
        
        self.numpy_to_raw(data, self.TEST_RAW_PATH)
        bin_data(self.DATA_SOURCE_FOLDER_NAME, 1, 5, 2)
        binned_data = get_raw_data(self.DATA_SOURCE_FOLDER_NAME, 0)
        expected_result:np.ndarray = np.array([[[2, 2], [3, 3], [3, 1]],
                                               [[3, 2], [2, 2], [2, 2]],
                                               [[2, 3], [1, 1], [3, 3]]])
        assert expected_result.all() == binned_data.all()
        
    def numpy_to_raw(self, array:np.ndarray, path: str):
        """Writes a numpy array to a raw file.
        
        :param array: The array to write.
        :param path: The path to write the file to.
        """
        array.flatten().tofile(path)