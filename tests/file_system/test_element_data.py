import sys

from os.path import join
from pathlib import Path

from numpy import ndarray, empty, array_equal
from pytest import raises
from werkzeug.datastructures.file_storage import FileStorage

sys.path.append('.')

from xrf_explorer.server.file_system.remove_this import \
    get_element_names, get_element_averages, get_elemental_datacube, get_elemental_datacube_dimensions

RESOURCES_PATH: Path = Path('tests', 'resources')


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
        result: list[str] = get_element_names("imaginary-config-file.yml")
        
        # verify
        assert len(result) == 0
        assert expected_output in caplog.text

    def test_config_not_found_raw(self, caplog):
        # setup
        expected_output: str = "Failed to access config"

        # execute
        result: ndarray = get_elemental_datacube("imaginary-config-file.yml")
        
        # verify
        assert array_equal(result, empty(0))
        assert expected_output in caplog.text

    def test_config_not_found_averages(self, caplog):
        # setup
        expected_output: str = "Failed to access config"

        # execute
        result: list[dict[str, str | float]] = get_element_averages("imaginary-config-file.yml")
        
        # verify
        assert len(result) == 0
        assert expected_output in caplog.text

    def test_file_not_found_names(self, caplog):
        # setup
        expected_output: str = "Could not read elemental data file"

        # execute
        result: list[str] = get_element_names(self.CUSTOM_CONFIG_PATH)
        
        # verify
        assert len(result) == 0
        assert expected_output in caplog.text

    def test_file_not_found_raw(self, caplog):
        # setup
        expected_output: str = "Could not read elemental data file"
        
        # execute
        result: ndarray = get_elemental_datacube(self.CUSTOM_CONFIG_PATH)
        
        # verify
        assert array_equal(result, empty(0))
        assert expected_output in caplog.text

    def test_file_not_found_averages(self, caplog):
        # setup
        expected_output: str = "Couldn't parse elemental image cube or list of names"
        
        # execute
        result: list[dict[str, str | float]] = get_element_averages(self.CUSTOM_CONFIG_PATH)
        
        # verify
        assert len(result) == 0
        assert expected_output in caplog.text

    def test_file_not_found_dimensions(self):
        # setup
        expected_output: str = "failed to decode header using \'ascii\' encoding"
        
        # execute
        with raises(UnicodeError) as e:
            get_elemental_datacube_dimensions("imaginary-file.dms")
        
        # verify
        assert expected_output in str(e.value)
