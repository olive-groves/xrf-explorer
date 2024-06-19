from os import mkdir
from os.path import join, isdir

from werkzeug.datastructures.file_storage import FileStorage

from xrf_explorer.server.file_system.helper import set_config, get_config
from xrf_explorer.server.file_system.sources.data_listing import get_data_sources_names

RESOURCES_PATH: str = join('tests', 'resources')


class TestUploadFileToServer:
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, 'configs', 'upload-file-server-backend.yml')
    CUSTOM_CONFIG_PATH_NO_SOURCES: str = join(RESOURCES_PATH, 'configs', 'upload-file-server-backend-no-sources.yml')
    UPLOAD_FILE_PATH: str = join(RESOURCES_PATH, 'file_system', 'txt-file.txt')

    @staticmethod
    def get_filestorage_object(path: str):
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
        config: dict = get_config()
        if not isdir(config["uploads-folder"]):
            mkdir(config["uploads-folder"])

        # execute
        result: list[str] = get_data_sources_names()

        # validate
        assert result == []
