from os import mkdir, path
import sys

from os.path import join
from pathlib import Path

from werkzeug.datastructures.file_storage import FileStorage

from xrf_explorer.server.file_system.config_handler import set_config, get_config

sys.path.append('.')

from xrf_explorer.server.file_system.data_listing import get_data_sources_names

RESOURCES_PATH: Path = Path('tests/resources')


class TestUploadFileToServer:
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, Path('configs/upload-file-server-backend.yml'))
    CUSTOM_CONFIG_PATH_NO_SOURCES: str = join(RESOURCES_PATH, Path('configs/upload-file-server-backend-no-sources.yml'))
    UPLOAD_FILE_PATH: str = join(RESOURCES_PATH, 'file_system/txt-file.txt')

    def get_filestorage_object(self, path: str):
        with open(path, 'rb') as f:
            file_storage: FileStorage = FileStorage(f)
        return file_storage

    def test_get_file_names(self):
        # setup
        data_source_name: str = "test_data_source"
        set_config(self.CUSTOM_CONFIG_PATH)

        # execute
        result: list[str] = get_data_sources_names()
        
        # validate
        assert data_source_name in result
    
    def test_no_file_names(self):
        # setup
        set_config(self.CUSTOM_CONFIG_PATH_NO_SOURCES)
        if not path.isdir(get_config()["uploads-folder"]):
            mkdir(get_config()["uploads-folder"])

        # execute
        result: list[str] = get_data_sources_names()

        # validate
        assert result == []
