from os import remove
from os.path import join
from pathlib import Path

from werkzeug.datastructures.file_storage import FileStorage
from xrf_explorer.server.file_system.config_handler import load_yml
from xrf_explorer.server.file_system.file_upload import upload_file_to_server
from xrf_explorer.server.file_system.get_files import get_files

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
        # constants
        filename: str = "test_file_name.txt"

        # open file
        f = open(self.UPLOAD_FILE_PATH, "rb")
        
        # setup
        file: FileStorage = FileStorage(f)
        file.filename = FILENAME

        # upload file
        result: bool = upload_file_to_server(file, self.CUSTOM_CONFIG_PATH)
        
        # close file
        file.close()

        # check if upload file was succussful
        assert bool

        # get files from server
        result: list[str] = get_files(self.CUSTOM_CONFIG_PATH)
        
        # Check if file was uploaded
        assert FILENAME in result

        # remove test file 
        config: dict = load_yml(self.CUSTOM_CONFIG_PATH)
        
        assert config

        remove(Path(config['uploads-folder'], FILENAME))
