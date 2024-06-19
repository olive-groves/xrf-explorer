from logging import INFO

from os import remove
from os.path import join

from numpy import ndarray, array_equal, array, float32

from xrf_explorer.server.file_system import set_config, get_config

from xrf_explorer.server.file_system import (
    get_elemental_data_cube, get_elemental_map, 
    get_element_names, get_element_averages,
    to_dms    
)

RESOURCES_PATH: str = join('tests', 'resources')


class TestElementalData:
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, 'configs', 'elemental-data.yml')

    DATA_CUBE_DMS: str = 'test.dms'
    DATA_CUBE_CSV: str = 'test.csv'
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
        
        # load custom config
        set_config(self.CUSTOM_CONFIG_PATH)
        custom_config: dict = get_config()
        path: str = join(custom_config["uploads-folder"], source)

        # execute
        result: list[str] = get_element_names(path)
        
        # verify
        assert len(result) == 2
        assert result == self.ELEMENTS
        assert expected_output in caplog.text
    
    def do_test_get_elemental_cube(self, source, caplog):
        caplog.set_level(INFO)

        # setup
        expected_output: str = f"Elemental data cube loaded. Shape: {self.RAW_ELEMENTAL_CUBE.shape}"
        
        # load custom config
        set_config(self.CUSTOM_CONFIG_PATH)
        custom_config: dict = get_config()
        path: str = str(join(custom_config["uploads-folder"], source))

        # execute
        result: ndarray = get_elemental_data_cube(path)
        
        # verify
        assert array_equal(result, self.RAW_ELEMENTAL_CUBE)
        assert expected_output in caplog.text

    def do_test_get_elemental_map(self, source, caplog):
        caplog.set_level(INFO)

        # setup
        elemental_map: ndarray = self.RAW_ELEMENTAL_CUBE[0]
        expected_output: str = f"Elemental map loaded. Shape: {elemental_map.shape}"
        
        # load custom config
        set_config(self.CUSTOM_CONFIG_PATH)
        custom_config: dict = get_config()
        path: str = str(join(custom_config["uploads-folder"], source))

        # execute
        result: ndarray = get_elemental_map(0, path)
        
        # verify
        assert array_equal(result, elemental_map)
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
        
        # load custom config
        set_config(self.CUSTOM_CONFIG_PATH)
        custom_config: dict = get_config()
        path: str = join(custom_config["uploads-folder"], self.DATA_CUBE_DMS)
        
        # execute
        result: list[dict[str, str | float]] = get_element_averages(path)
        
        # verify
        assert len(result) == 2
        assert result[0]['name'] == self.ELEMENTS[0]
        assert result[1]['name'] == self.ELEMENTS[1]
        assert expected_output in caplog.text

    def test_csv_to_dms(self, caplog):
        # setup
        set_config(self.CUSTOM_CONFIG_PATH)
        folder_path: str = join(RESOURCES_PATH, "file_system", "test_elemental_data")

        # execute
        result: bool = to_dms(folder_path, self.NAME_CUBE_FROM_CSV, self.RAW_ELEMENTAL_CUBE, self.ELEMENTS)

        # verify
        assert result
        self.do_test_get_element_names(self.NAME_CUBE_FROM_CSV + '.dms', caplog)
        self.do_test_get_elemental_cube(self.NAME_CUBE_FROM_CSV + '.dms', caplog)

        # cleanup
        remove(join(folder_path, self.NAME_CUBE_FROM_CSV + '.dms'))
