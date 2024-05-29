from logging import INFO

import sys

from os import remove
from os.path import join
from pathlib import Path

from numpy import ndarray, empty, array_equal, array, float32

sys.path.append('.')

from xrf_explorer.server.file_system import (
    get_elemental_data_cube, get_elemental_map, 
    get_element_names, get_element_averages,
    to_dms    
)

RESOURCES_PATH: Path = Path('tests', 'resources')


class TestElementalData:
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, Path('configs', 'elemental-data.yml'))

    DATA_CUBE_DMS: str = '../resources/file_system/test_elemental_data/test.dms'
    DATA_CUBE_CSV: str = '../resources/file_system/test_elemental_data/test.csv'
    NAME_CUBE_FROM_CSV: str = 'cube_from_csv'
    NON_EXISTING_CUBE: str = 'non-existing.dms'

    ELEMENTS: list[str] = ["Secret", "Element"]
    RAW_ELEMENTAL_CUBE: ndarray = array([
        [[-1, -2, -3], [-4, -5, -6], [-7, -8, -9]], 
        [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        ], dtype=float32)

    def do_test_get_element_names(self, source, caplog):
        caplog.set_level(INFO)

        # setup
        expected_output: str = f"Elements loaded. Total elements: {len(self.ELEMENTS)}"

        # execute
        result: list[str] = get_element_names(source, self.CUSTOM_CONFIG_PATH)
        
        # verify
        assert len(result) == 2
        assert result == self.ELEMENTS
        assert expected_output in caplog.text
    
    def do_test_get_elemental_cube(self, source, caplog):
        caplog.set_level(INFO)

        # setup
        expected_output: str = f"Elemental data cube loaded. Shape: {self.RAW_ELEMENTAL_CUBE.shape}"

        # execute
        result: ndarray = get_elemental_data_cube(source, self.CUSTOM_CONFIG_PATH)
        
        # verify
        assert array_equal(result, self.RAW_ELEMENTAL_CUBE)
        assert expected_output in caplog.text

    def do_test_get_elemental_map(self, source, caplog):
        caplog.set_level(INFO)

        # setup
        elemental_map: ndarray = self.RAW_ELEMENTAL_CUBE[0]
        expected_output: str = f"Elemental map loaded. Shape: {elemental_map.shape}"

        # execute
        result: ndarray = get_elemental_map(0, source, self.CUSTOM_CONFIG_PATH)
        
        # verify
        assert array_equal(result, elemental_map)
        assert expected_output in caplog.text

    def test_config_not_found_names(self, caplog):
        # setup
        expected_output: str = "Failed to access config"

        # execute
        result: list[str] = get_element_names(self.DATA_CUBE_DMS, "imaginary-config-file.yml")
        
        # verify
        assert len(result) == 0
        assert expected_output in caplog.text

    def test_config_not_found_raw(self, caplog):
        # setup
        expected_output: str = "Failed to access config"

        # execute
        result: ndarray = get_elemental_data_cube(self.DATA_CUBE_DMS, "imaginary-config-file.yml")
        
        # verify
        assert array_equal(result, empty(0))
        assert expected_output in caplog.text
    
    def test_config_not_found_elemental_map(self, caplog):
        # setup
        expected_output: str = "Failed to access config"

        # execute
        result: ndarray = get_elemental_map(0, self.DATA_CUBE_DMS, "imaginary-config-file.yml")
        
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

    def test_config_not_found_to_dms(self, caplog):
        # setup
        expected_output: str = "Failed to access config"

        # execute
        result: bool = to_dms(self.NAME_CUBE_FROM_CSV, self.RAW_ELEMENTAL_CUBE, self.ELEMENTS, "imaginary-config-file.yml")

        # verify
        assert not result
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
    
    def test_file_not_found_elemental_map(self, caplog):
        # setup
        expected_output: str = "File not found"

        # execute
        result: ndarray = get_elemental_map(0, self.NON_EXISTING_CUBE, self.CUSTOM_CONFIG_PATH)
        
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
    
    def test_to_dms_invalid_file_name_with_extension(self, caplog):
        # setup
        expected_output: str = "Name of the cube should not contain a file extension."

        # execute
        result: bool = to_dms("invalid.test", self.RAW_ELEMENTAL_CUBE, self.ELEMENTS, self.CUSTOM_CONFIG_PATH)

        # verify
        assert not result
        assert expected_output in caplog.text

    def test_get_element_names(self, caplog):
        self.do_test_get_element_names(self.DATA_CUBE_DMS, caplog)
        self.do_test_get_element_names(self.DATA_CUBE_CSV, caplog)
    
    def test_get_elemental_cube(self, caplog):
        self.do_test_get_elemental_cube(self.DATA_CUBE_DMS, caplog)
        self.do_test_get_elemental_cube(self.DATA_CUBE_CSV, caplog)

    def test_get_elemental_map(self, caplog):
        self.do_test_get_elemental_map(self.DATA_CUBE_DMS, caplog)
        self.do_test_get_elemental_map(self.DATA_CUBE_CSV, caplog)

    def test_get_element_averages(self, caplog):
        caplog.set_level(INFO)

        # setup
        expected_output: str = "Calculated the average composition of the elements."
        
        # execute
        result: list[dict[str, str | float]] = get_element_averages(self.DATA_CUBE_DMS, self.CUSTOM_CONFIG_PATH)
        
        # verify
        assert len(result) == 2
        assert result[0]['name'] == self.ELEMENTS[0]
        assert result[1]['name'] == self.ELEMENTS[1]
        assert expected_output in caplog.text

    def test_csv_to_dms(self, caplog):
        # execute
        result: bool = to_dms(self.NAME_CUBE_FROM_CSV, self.RAW_ELEMENTAL_CUBE, self.ELEMENTS, self.CUSTOM_CONFIG_PATH)

        # verify
        assert result
        self.do_test_get_element_names(self.NAME_CUBE_FROM_CSV + '.dms', caplog)
        self.do_test_get_elemental_cube(self.NAME_CUBE_FROM_CSV + '.dms', caplog)

        # cleanup
        remove(join(RESOURCES_PATH, "file_system", "test_elemental_data", self.NAME_CUBE_FROM_CSV + '.dms'))
