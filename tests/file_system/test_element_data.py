import sys

from os.path import join
from pathlib import Path
from numpy import ndarray, empty, array_equal

from werkzeug.datastructures.file_storage import FileStorage

sys.path.append('.')

from xrf_explorer.server.file_system.element_data import get_element_names, get_element_averages, get_raw_elemental_data

RESOURCES_PATH: Path = Path('tests/resources')

class TestElementalData:
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, Path('configs/elemental-data.yml'))

    def get_filestorage_object(self, path: str) -> FileStorage:
        with open(path, 'rb') as f:
            file_storage: FileStorage = FileStorage(f)
        return file_storage

    def test_config_not_found(self, caplog):
        # setup
        expected_output: str = "Failed to access config"

        # execute
        result: list[str] = get_element_names("imaginary-config-file.yml")
        
        # verify
        assert result == []
        assert expected_output in caplog.text

    def test_file_not_found_names(self, caplog):
        # setup
        expected_output: str = "Couldn't read elemental data file"

        # execute
        result: list[str] = get_element_names(self.CUSTOM_CONFIG_PATH)
        
        # verify
        assert result == []
        assert expected_output in caplog.text

    def test_file_not_found_raw(self, caplog):
        # setup
        expected_output: str = "Could not find elemental data"
        
        # execute
        result: ndarray = get_raw_elemental_data(self.CUSTOM_CONFIG_PATH)
        
        # verify
        assert array_equal(result, empty(0))
        assert expected_output in caplog.text