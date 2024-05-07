from os import getlogin
from os.path import exists, join
from pathlib import Path
from shutil import copyfile

import yaml

from werkzeug.datastructures.file_storage import FileStorage

from xrf_explorer.server.file_system.file_upload import remove_local_file, upload_file_to_server

RESOURCES_PATH: Path = Path('tests/resources')


class TestRemoveLocalFile:

    def test_basic(self, tmp_path):
        # setup
        path_to_be_removed: str = join(tmp_path, 'remove.txt')
        copyfile(join(RESOURCES_PATH, Path('file_system/txt-file.txt')), path_to_be_removed)

        # execute
        result: bool = remove_local_file(path_to_be_removed)

        # verify
        assert result
        assert not exists(path_to_be_removed)

    def test_non_existent_file(self, capsys):
        # setup
        path_to_be_removed: str = 'this-path-does-not-exist.txt'
        expected_output: str = "Could not find temporary file {this-path-does-not-exist.txt} for removal"

        # execute
        result: bool = remove_local_file(path_to_be_removed)
        captured_output = capsys.readouterr()

        print(captured_output.err)

        # verify
        assert not result
        assert expected_output in captured_output.err


class TestUploadFileToServer:
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, Path('configs/upload-file-server-backend.yml'))
    UPLOAD_FILE_PATH: str = join(RESOURCES_PATH, 'file_system/txt-file.txt')

    def get_filestorage_object(self, path: str):
        with open(path, 'rb') as f:
            file_storage: FileStorage = FileStorage(f)
        return file_storage

    def load_custom_config(self):
        with open(self.CUSTOM_CONFIG_PATH, 'rb') as file:
            return yaml.safe_load(file)

    def set_new_config_values(self, cfg: dict, temp_path):
        cfg['storage-server']['user'] = getlogin()
        cfg['storage-server']['path'] = join(temp_path, cfg['storage-server']['path'])
        cfg['backend']['temp-folder'] = join(temp_path, cfg['backend']['temp-folder'])
        return cfg


    def dict_to_yml(self, dictionary: dict, output_path: str):
        with open(output_path, 'w') as new_yml_file:
            yaml.dump(dictionary, new_yml_file, default_flow_style=False)

    def test_basic(self, tmp_path, capsys):
        # setup
        config: dict = self.load_custom_config()
        # set new values
        config = self.set_new_config_values(config.copy(), tmp_path)
        # dump new config to a new file
        new_config_path: str = join(tmp_path, 'custom_config.yml')
        self.dict_to_yml(config, new_config_path)
        # create FileStorage object
        file: FileStorage = self.get_filestorage_object(self.UPLOAD_FILE_PATH)

        expected_output: str = \
            f"Uploaded {{{self.UPLOAD_FILE_PATH}}} to {{{config['storage-server']['path']}/text-file.txt}}"

        # execute
        result: bool = upload_file_to_server(file, new_config_path)
        captured_output = capsys.readouterr()

        # verify
        assert result
        assert expected_output in captured_output.out

    def test_config_not_found(self, capsys):
        # setup
        file: FileStorage = self.get_filestorage_object(self.UPLOAD_FILE_PATH)
        expected_output: str = f"Failed to access backend config at {{this-config-does-not-exist.yml}}"

        # execute
        result: bool = upload_file_to_server(file, 'this-config-does-not-exist.yml')
        captured_output = capsys.readouterr()

        # verify
        assert not result
        assert expected_output in captured_output.err

    def test_invalid_filename(self, capsys):
        # setup
        file: FileStorage = self.get_filestorage_object('')
        expected_output: str = "Could not parse provided file name"

        # execute
        result: bool = upload_file_to_server(file, self.CUSTOM_CONFIG_PATH)
        capture_output = capsys.readouterr()

        # validate
        assert not result
        assert expected_output in capture_output.err

    def test_unreachable_server(self, tmp_path, capsys):
        # setup
        config: dict = self.load_custom_config()
        # set new values
        config = self.set_new_config_values(config.copy(), tmp_path)
        config['storage-server']['ip'] = '333.333.333.333'
        # dump new config to a new file
        new_config_path: str = join(tmp_path, 'custom_config.yml')
        self.dict_to_yml(config, new_config_path)
        # create FileStorage object
        file: FileStorage = self.get_filestorage_object(self.UPLOAD_FILE_PATH)

        expected_output: str = "Failed to establish SSH connection to remote storage server"

        # execute
        result: bool = upload_file_to_server(file, new_config_path)
        captured_output = capsys.readouterr()

        # validate
        assert not result
        assert expected_output in captured_output.err
