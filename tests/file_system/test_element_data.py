from logging import INFO

import sys

from os.path import join
from pathlib import Path

from numpy import ndarray, empty, array_equal, array, float32

sys.path.append('.')

from xrf_explorer.server.file_system.elemental_cube import get_element_names, get_element_averages, get_elemental_data_cube

RESOURCES_PATH: Path = Path('tests', 'resources')


class TestElementalData:
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, Path('configs', 'elemental-data.yml'))

    DATA_CUBE: str = 'test.dms'
    NON_EXISTING_CUBE: str = 'non-existing.dms'

    ELEMENTS: list[str] = ["Secret", "Element"]
    RAW_ELEMENTAL_CUBE: ndarray = array([
        [[-1, -2, -3], [-4, -5, -6], [-7, -8, -9]], 
        [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        ], dtype=float32)


    def test_config_not_found_names(self, caplog):
        # setup
        expected_output: str = "Failed to access config"

        # execute
        result: list[str] = get_element_names(self.DATA_CUBE, "imaginary-config-file.yml")
        
        # verify
        assert len(result) == 0
        assert expected_output in caplog.text

    def test_config_not_found_raw(self, caplog):
        # setup
        expected_output: str = "Failed to access config"

        # execute
        result: ndarray = get_elemental_data_cube(self.DATA_CUBE, "imaginary-config-file.yml")
        
        # verify
        assert array_equal(result, empty(0))
        assert expected_output in caplog.text

    def test_config_not_found_averages(self, caplog):
        # setup
        expected_output: str = "Failed to access config"

        # execute
        result: list[dict[str, str | float]] = get_element_averages(self.NON_EXISTING_CUBE, "imaginary-config-file.yml")
        
        # verify
        assert len(result) == 0
        assert expected_output in caplog.text

    def test_file_not_found_names(self, caplog):
        # setup
        expected_output: str = "File not found"

        # execute
        result: list[str] = get_element_names(self.NON_EXISTING_CUBE, self.CUSTOM_CONFIG_PATH)
        
        # verify
        assert len(result) == 0
        assert expected_output in caplog.text

    def test_file_not_found_raw(self, caplog):
        # setup
        expected_output: str = "File not found"
        
        # execute
        result: ndarray = get_elemental_data_cube(self.NON_EXISTING_CUBE, self.CUSTOM_CONFIG_PATH)
        
        # verify
        assert array_equal(result, empty(0))
        assert expected_output in caplog.text

    def test_file_not_found_averages(self, caplog):
        # setup
        expected_output: str = "Couldn't parse elemental image cube or list of names"
        
        # execute
        result: list[dict[str, str | float]] = get_element_averages(self.NON_EXISTING_CUBE, self.CUSTOM_CONFIG_PATH)
        
        # verify
        assert len(result) == 0
        assert expected_output in caplog.text

    def test_get_element_names(self, caplog):
        caplog.set_level(INFO)

        # setup
        expected_output: str = f"Elements loaded. Total elements: {len(self.ELEMENTS)}"

        # execute
        result: list[str] = get_element_names(self.DATA_CUBE, self.CUSTOM_CONFIG_PATH)
        
        # verify
        assert len(result) == 2
        assert result == self.ELEMENTS
        assert expected_output in caplog.text
    
    def test_get_elemental_cube(self, caplog):
        caplog.set_level(INFO)

        # setup
        expected_output: str = f"Elemental data cube loaded. Shape: {self.RAW_ELEMENTAL_CUBE.shape}"

        # execute
        result: ndarray = get_elemental_data_cube(self.DATA_CUBE, self.CUSTOM_CONFIG_PATH)
        
        # verify
        assert array_equal(result, self.RAW_ELEMENTAL_CUBE)
        assert expected_output in caplog.text

    def test_get_element_averages(self, caplog):
        caplog.set_level(INFO)

        # setup
        expected_output: str = "Calculated the average composition of the elements."
        
        # execute
        result: list[dict[str, str | float]] = get_element_averages(self.DATA_CUBE, self.CUSTOM_CONFIG_PATH)
        
        # verify
        assert len(result) == 2
        assert result[0]['name'] == self.ELEMENTS[0]
        assert result[1]['name'] == self.ELEMENTS[1]
        assert expected_output in caplog.text