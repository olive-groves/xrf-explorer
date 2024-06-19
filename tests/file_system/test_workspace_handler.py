from logging import INFO

from os import remove
from os.path import join, normpath

from json import load

from xrf_explorer.server.file_system.helper import set_config
from xrf_explorer.server.file_system import get_path_to_workspace, update_workspace

RESOURCES_PATH: str = join('tests', 'resources')


class TestWorkspaceHandler:
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, 'configs', 'workspace_handler.yml')
    CUSTOM_DATA_FOLDER: str = join(RESOURCES_PATH, 'file_system', 'test_workspace_handler')
    DATASOURCE_NAME: str = "a_datasource"
    DATASOURCE_NAME_NO_WORKSPACE: str = "no_datasource"

    def test_config_not_found_get_workspace(self, caplog):
        # setup
        expected_output: str = "Failed to access config"
        set_config("imaginary-config-file.yml")

        # execute
        result: str = get_path_to_workspace(self.DATASOURCE_NAME, )
        
        # verify
        assert not result
        assert expected_output in caplog.text
    
    def test_config_not_found_update_workspace(self, caplog):
        # setup
        expected_output: str = "Failed to access config"
        new_workspace: dict = {"message": "Hi!"}
        set_config("imaginary-config-file.yml")

        # execute
        result: bool = update_workspace(self.DATASOURCE_NAME_NO_WORKSPACE, new_workspace)
        
        # verify
        assert not result
        assert expected_output in caplog.text

    def test_datasource_not_found_get_workspace(self, caplog):
        # setup
        expected_output: str = "Datasource this_is_not_a_datasource not found."
        set_config(self.CUSTOM_CONFIG_PATH)

        # execute
        result: str = get_path_to_workspace("this_is_not_a_datasource")
        
        # verify
        assert not result
        assert expected_output in caplog.text
    
    def test_datasource_not_found_update_workspace(self, caplog):
        # setup
        expected_output: str = "Datasource this_is_not_a_datasource not found."
        new_workspace: dict = {"message": "Hi!"}
        set_config(self.CUSTOM_CONFIG_PATH)

        # execute
        result: bool = update_workspace("this_is_not_a_datasource", new_workspace)
        
        # verify
        assert not result
        assert expected_output in caplog.text

    def test_workspace_found(self, caplog):
        caplog.set_level(INFO)

        # setup
        expected_output: str = f"Workspace {self.DATASOURCE_NAME} found."
        set_config(self.CUSTOM_CONFIG_PATH)

        # execute
        result: str = get_path_to_workspace(self.DATASOURCE_NAME)
        
        # verify
        assert normpath(join(self.CUSTOM_DATA_FOLDER, self.DATASOURCE_NAME, 'workspace.json')) == normpath(result)
        assert expected_output in caplog.text
    
    def test_update_workspace(self, caplog):
        caplog.set_level(INFO)

        # setup
        expected_output: str = f"Data written to workspace {self.DATASOURCE_NAME_NO_WORKSPACE} successfully"
        new_workspace: dict = {"message": "Hi!"}
        set_config(self.CUSTOM_CONFIG_PATH)

        # execute
        result: bool = update_workspace(self.DATASOURCE_NAME_NO_WORKSPACE, new_workspace)
        
        # verify
        assert result
        assert expected_output in caplog.text
        
        # verify json
        path_to_workspace: str = join(self.CUSTOM_DATA_FOLDER, self.DATASOURCE_NAME_NO_WORKSPACE, 'workspace.json')
        with open(path_to_workspace, 'r') as f:
            data: any = load(f)
            assert data["message"] == "Hi!"

        # cleanup
        remove(path_to_workspace)
