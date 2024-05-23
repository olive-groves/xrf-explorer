import sys

from os.path import join
from pathlib import Path

from numpy import ndarray, empty, array_equal
from werkzeug.datastructures.file_storage import FileStorage

sys.path.append('.')

from xrf_explorer.server.file_system.elemental_cube import get_short_element_names, get_element_averages, get_elemental_data_cube

RESOURCES_PATH: Path = Path('tests', 'resources')
DATA_CUBE_NAME: str = '196_1989_M6_elemental_datacube_1069_1187_rotated_inverted.dms'


class TestElementalData:
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, Path('configs', 'elemental-data.yml'))

    def get_filestorage_object(self, path: str) -> FileStorage:
        with open(path, 'rb') as f:
            file_storage: FileStorage = FileStorage(f)
        return file_storage

    def test_config_not_found_names(self, caplog):
        # setup
        expected_output: str = "Failed to access config"

        # execute
        result: list[str] = get_short_element_names(DATA_CUBE_NAME, "imaginary-config-file.yml")
        
        # verify
        assert len(result) == 0
        assert expected_output in caplog.text

    def test_config_not_found_raw(self, caplog):
        # setup
        expected_output: str = "Failed to access config"

        # execute
        result: ndarray = get_elemental_data_cube(DATA_CUBE_NAME, "imaginary-config-file.yml")
        
        # verify
        assert array_equal(result, empty(0))
        assert expected_output in caplog.text

    def test_config_not_found_averages(self, caplog):
        # setup
        expected_output: str = "Failed to access config"

        # execute
        result: list[dict[str, str | float]] = get_element_averages(DATA_CUBE_NAME, "imaginary-config-file.yml")
        
        # verify
        assert len(result) == 0
        assert expected_output in caplog.text

    def test_file_not_found_names(self, caplog):
        # setup
        expected_output: str = "File not found"

        # execute
        result: list[str] = get_short_element_names(DATA_CUBE_NAME, self.CUSTOM_CONFIG_PATH)
        
        # verify
        assert len(result) == 0
        assert expected_output in caplog.text

    def test_file_not_found_raw(self, caplog):
        # setup
        expected_output: str = "File not found"
        
        # execute
        result: ndarray = get_elemental_data_cube(DATA_CUBE_NAME, self.CUSTOM_CONFIG_PATH)
        
        # verify
        assert array_equal(result, empty(0))
        assert expected_output in caplog.text

    def test_file_not_found_averages(self, caplog):
        # setup
        expected_output: str = "Couldn't parse elemental image cube or list of names"
        
        # execute
        result: list[dict[str, str | float]] = get_element_averages(DATA_CUBE_NAME, self.CUSTOM_CONFIG_PATH)
        
        # verify
        assert len(result) == 0
        assert expected_output in caplog.text

