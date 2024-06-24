from ntpath import join
import numpy as np
import pytest

from xrf_explorer.server.file_system.cubes.spectral import parse_rpl, mipmap_exists, mipmap_raw_cube, get_raw_data, get_spectra_params, bin_data
from xrf_explorer.server.file_system.helper import set_config
from xrf_explorer.server.file_system.workspace.file_access import get_raw_rpl_paths


class TestSpectral:
    RESOURCES_PATH: str = join('tests', 'resources')
    DATA_SOURCE_FOLDER_NAME: str = "Data_source"
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, "configs", "spectra.yml")
    TEST_RAW_PATH: str = join(RESOURCES_PATH, "spectra", "data", "Data_source", "data.raw")
    
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
            "depth": "16",
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
        
        expected_params: dict = {
            "low": 0,
            "high": 8,
            "binSize": 2
            }
        
        assert params == expected_params
        
    def test_get_spectra_params_file_not_found(self, caplog):
        
        with pytest.raises(FileNotFoundError) as err:
            params: dict = get_spectra_params("false_name")
            
        assert "" in str(err.value)
        