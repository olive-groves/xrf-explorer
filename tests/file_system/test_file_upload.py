import sys

from os.path import join
from pathlib import Path

from werkzeug.datastructures.file_storage import FileStorage

sys.path.append('.')

from xrf_explorer.server.file_system.file_upload import upload_file_to_server
from xrf_explorer.server.file_system.data_listing import get_data_sources_names

RESOURCES_PATH: Path = Path('tests/resources')


class TestUploadFileToServer:
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, Path('configs/upload-file-server-backend.yml'))
    UPLOAD_FILE_PATH: str = join(RESOURCES_PATH, 'file_system/txt-file.txt')

    def get_filestorage_object(self, path: str):
        with open(path, 'rb') as f:
            file_storage: FileStorage = FileStorage(f)
        return file_storage

    def test_config_not_found(self, caplog):
        # setup
        file: FileStorage = self.get_filestorage_object(self.UPLOAD_FILE_PATH)
        expected_output: str = "Failed to access config"

        # execute
        result: bool = upload_file_to_server(file, 'this-config-does-not-exist.yml')

        # verify
        assert not result
        assert expected_output in caplog.text

    def test_invalid_filename(self, caplog):
        # setup
        file: FileStorage = self.get_filestorage_object(self.UPLOAD_FILE_PATH)
        file.filename = ''
        expected_output: str = "Could not parse provided file name"

        # execute
        result: bool = upload_file_to_server(file, self.CUSTOM_CONFIG_PATH)

        # validate
        assert not result
        assert expected_output in caplog.text
    
    def test_get_file_names(self):
        # setup
        data_source_name: str = "test_data_source"

        # execute
        result: list[str] = get_data_sources_names(self.CUSTOM_CONFIG_PATH)
        
        # validate
        assert data_source_name in result
    
    def test_no_file_names(self):
        # execute
        result: list[str] = get_data_sources_names('this-config-does-not-exist.yml')

        # validate
        assert result == []