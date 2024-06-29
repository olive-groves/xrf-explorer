import json
from pathlib import Path

import numpy as np
import pytest

from xrf_explorer.server.file_system.cubes.spectral import (
    parse_rpl, 
    get_raw_data, 
    get_spectra_params, 
    bin_data, 
    update_bin_params
)
from xrf_explorer.server.file_system.helper import set_config
from xrf_explorer.server.file_system.workspace.file_access import get_raw_rpl_paths, get_workspace_dict
from xrf_explorer.server.file_system.workspace.workspace_handler import get_path_to_workspace


class TestSpectral:
    RESOURCES_PATH: Path = Path('tests', 'resources')
    DATA_SOURCE_FOLDER_NAME: str = "spectra_source"
    CUSTOM_CONFIG_PATH: str = str(Path(RESOURCES_PATH, "configs", "spectra.yml")).replace("\\", "/")
    TEST_RAW_PATH: str = (str(Path(RESOURCES_PATH, "spectra", "data", DATA_SOURCE_FOLDER_NAME, "data.raw"))  
                          .replace("\\", "/"))
    EMPTY_SOURCE_NAME: str = "empty_source"
    NO_RAW_SOURCE_NAME: str = "no_raw_source"
    WRONG_SIZE_NAME: str = "wrong_size_source"
    NO_OFFSET_NAME: str = "no_offset_source"
    NO_WORKSPACE_NAME: str = "wo_workspace_source"
    
    @pytest.fixture(autouse=True)
    def setup_environment(self):
        set_config(self.CUSTOM_CONFIG_PATH)
        yield
        
    def numpy_to_raw(self, array:np.ndarray, path: str):
        """Writes a numpy array to a raw file.
        
        :param array: The array to write.
        :param path: The path to write the file to.
        """
        array.flatten().tofile(path)
    
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
            "byte-order": "little-endian",
            "record-by": "vector",
            "depthbinsize": "1",
            "depth1": "200",
            "depth2": "3000",
            "depthscaleorigin": "-0.956",
            "depthscaleincrement": "0.010002",
            "depthscaleunits": "keV"
        }
        
        assert info == expected_info
    
    def test_parse_rpl_empty_file(self, caplog):
        
        _, path = get_raw_rpl_paths(self.EMPTY_SOURCE_NAME)
        info: dict = parse_rpl(path)
        expected_output: str = "Error while parsing rpl file: file empty\n"
        
        assert info == {}
        assert expected_output in caplog.text
        
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
            _: dict = get_spectra_params("false_name")
            
        assert "" in str(err.value)
        
    def test_update_bin_params_default(self):
        workspace_dict: dict | None = get_workspace_dict(self.WRONG_SIZE_NAME)
        if workspace_dict is not None:
            workspace_dict["spectralParams"]["low"] = 0
            workspace_dict["spectralParams"]["high"] = 40
            workspace_dict["spectralParams"]["binSize"] = 40 / 4096
            workspace_dict["spectralParams"]["binned"] = True
        
        workspace_path = get_path_to_workspace(self.WRONG_SIZE_NAME)

        with open(workspace_path, 'w') as f:
            json.dump(workspace_dict, f)
                 
        update_bin_params(self.WRONG_SIZE_NAME)
        
        params: dict = get_spectra_params(self.WRONG_SIZE_NAME)
        assert params == {'low': 0, 'high': 4096, 'binSize': 1, 'binned': True}
        
    def test_update_bin_params(self):
        workspace_dict: dict | None = get_workspace_dict(self.WRONG_SIZE_NAME)
        if workspace_dict is not None:
            workspace_dict["spectralParams"]["low"] = 0.5
            workspace_dict["spectralParams"]["high"] = 20
            workspace_dict["spectralParams"]["binSize"] = 0.05
            workspace_dict["spectralParams"]["binned"] = True
        
        workspace_path = get_path_to_workspace(self.WRONG_SIZE_NAME)

        with open(workspace_path, 'w') as f:
            json.dump(workspace_dict, f)
                 
        update_bin_params(self.WRONG_SIZE_NAME)
        
        params: dict = get_spectra_params(self.WRONG_SIZE_NAME)
        assert params == {'low': 51, 'high': 2048, 'binSize': 6, 'binned': True}
        
    def test_update_bin_params_no_offset(self):
        workspace_dict: dict | None = get_workspace_dict(self.NO_OFFSET_NAME)
        if workspace_dict is not None:
            workspace_dict["spectralParams"]["low"] = 0.5
            workspace_dict["spectralParams"]["high"] = 20
            workspace_dict["spectralParams"]["binSize"] = 0.05
            workspace_dict["spectralParams"]["binned"] = True
        
        workspace_path = get_path_to_workspace(self.NO_OFFSET_NAME)

        with open(workspace_path, 'w') as f:
            json.dump(workspace_dict, f)
                 
        update_bin_params(self.NO_OFFSET_NAME)
        
        params: dict = get_spectra_params(self.NO_OFFSET_NAME)
        assert params == {'low': 51, 'high': 2048, 'binSize': 6, 'binned': True}

    
    def test_bin_data_identity(self):
        # setup
        data: np.ndarray = np.array([[[3, 1, 3, 4, 0, 4], [1, 2, 4, 4, 0, 4], [1, 2, 4, 4, 0, 4]],
                                     [[2, 2, 4, 4, 0, 4], [2, 1, 3, 4, 0, 4], [2, 1, 3, 4, 0, 4]],
                                     [[2, 1, 3, 4, 0, 4], [2, 0, 2, 4, 0, 4], [2, 2, 4, 4, 0, 4]]], dtype=np.uint16)
        
        self.numpy_to_raw(data, self.TEST_RAW_PATH)
        
        # execute
        bin_data(self.DATA_SOURCE_FOLDER_NAME, 0, 2, 1)
        binned_data = get_raw_data(self.DATA_SOURCE_FOLDER_NAME, 0)
        
        # verify
        assert data.all() == binned_data.all()
        
    def test_bin_data_(self):
        # setup
        data: np.ndarray = np.array([[[3, 1, 3, 4, 0, 4], [1, 2, 4, 4, 2, 4], [1, 2, 4, 2, 0, 4]],
                                     [[2, 2, 4, 4, 0, 4], [2, 1, 3, 3, 1, 4], [2, 1, 3, 4, 0, 4]],
                                     [[2, 1, 3, 4, 2, 4], [2, 0, 2, 2, 0, 4], [2, 2, 4, 4, 2, 4]]], dtype=np.uint16)
        
        self.numpy_to_raw(data, self.TEST_RAW_PATH)
        
        # execute
        bin_data(self.DATA_SOURCE_FOLDER_NAME, 1, 5, 2)
        binned_data = get_raw_data(self.DATA_SOURCE_FOLDER_NAME, 0)
        expected_result: np.ndarray = np.array([[[2, 2], [3, 3], [3, 1]],
                                               [[3, 2], [2, 2], [2, 2]],
                                               [[2, 3], [1, 1], [3, 3]]])

        # verify
        assert expected_result.all() == binned_data.all()
    
    def test_bin_data_default_params(self):
        # setup
        data: np.ndarray = np.array([[[2, 2], [3, 3], [3, 1]],
                                     [[3, 2], [2, 2], [2, 2]],
                                     [[2, 3], [1, 1], [3, 3]]], dtype=np.uint16)
        self.numpy_to_raw(data, self.TEST_RAW_PATH)
        
        workspace_dict: dict | None = get_workspace_dict(self.WRONG_SIZE_NAME)
        if workspace_dict is not None:
            workspace_dict["spectralParams"]["binned"] = False
        
        workspace_path = get_path_to_workspace(self.WRONG_SIZE_NAME)
        with open(workspace_path, 'w') as f:
            json.dump(workspace_dict, f)
        
        # execute
        bin_data(self.DATA_SOURCE_FOLDER_NAME, 0, 4096, 1)
        binned_data = get_raw_data(self.DATA_SOURCE_FOLDER_NAME, 0)
        params = get_spectra_params(self.DATA_SOURCE_FOLDER_NAME)
        
        # assert
        assert binned_data.all() == data.all()
        assert params["binned"]

    def test_bin_data_empty_rpl(self, caplog):
        bin_data(self.EMPTY_SOURCE_NAME, 0, 4, 1)
        assert f"error while binning data: rpl is empty for {self.EMPTY_SOURCE_NAME}" in caplog.text
        
    def test_bin_data_wrong_size(self, caplog):
        bin_data(self.WRONG_SIZE_NAME, 0, 4, 1)
        assert "error while reshaping raw data: cannot reshape array of size 0 into shape (3,3,6)" in caplog.text  
    
    def test_bin_data_no_raw(self, caplog):
        
        with pytest.raises(OSError) as err:
            bin_data(self.NO_RAW_SOURCE_NAME, 0, 4, 1)
        
        assert "[Errno 2] No such file or directory" in str(err.value)
        assert "error while loading raw file for binning:" in caplog.text
