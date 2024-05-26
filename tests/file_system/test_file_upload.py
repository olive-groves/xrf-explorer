import sys

from os.path import join
from pathlib import Path

from werkzeug.datastructures.file_storage import FileStorage

sys.path.append('.')

from xrf_explorer.server.file_system.data_listing import get_data_sources_names

RESOURCES_PATH: Path = Path('tests/resources')


class TestUploadFileToServer:
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, Path('configs/upload-file-server-backend.yml'))
    UPLOAD_FILE_PATH: str = join(RESOURCES_PATH, 'file_system/txt-file.txt')

    def get_filestorage_object(self, path: str):
        with open(path, 'rb') as f:
            file_storage: FileStorage = FileStorage(f)
        return file_storage

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
