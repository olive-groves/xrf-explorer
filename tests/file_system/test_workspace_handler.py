from json import load
from logging import INFO
from os import remove
from os.path import join, normpath

from xrf_explorer.server.file_system import set_config
from xrf_explorer.server.file_system.workspace import (
    get_path_to_workspace, update_workspace, get_base_image_name, 
    get_base_image_path, get_workspace_dict, get_elemental_cube_path_from_name
)
from xrf_explorer.server.file_system.workspace.file_access import get_spectral_cube_recipe_path

RESOURCES_PATH: str = join('tests', 'resources')


class TestWorkspaceHandler:
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, 'configs', 'workspace_handler.yml')
    CUSTOM_DATA_FOLDER: str = join(RESOURCES_PATH, 'file_system', 'test_workspace_handler')
    DATASOURCE_NAME: str = "a_datasource"
    DATASOURCE_NAME_NO_WORKSPACE: str = "no_datasource"
    ELEMENTAL_CUBE_NAME: str = "elemental cube"

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

    def test_get_get_workspace_dict_no_config(self, caplog):
        # setup
        set_config("imaginary-config-file.yml")

        # execute
        result: str | None = get_workspace_dict(self.DATASOURCE_NAME)

        # verify
        assert result is None 
        assert "Config is empty" in caplog.text

    def test_get_spectral_cube_recipe_path_no_config(self, caplog):
        # setup
        set_config("imaginary-config-file.yml")

        # execute
        result: str | None = get_spectral_cube_recipe_path(self.DATASOURCE_NAME)

        # verify
        assert result is None 
        assert "Config is empty" in caplog.text
    
    def test_get_spectral_cube_recipe_path_no_workspace(self):
        # setup
        set_config(self.CUSTOM_CONFIG_PATH)

        # execute
        result: str | None = get_spectral_cube_recipe_path(self.DATASOURCE_NAME_NO_WORKSPACE)

        # verify
        assert result is None

    def test_get_base_image_name_no_config(self, caplog):
        # setup
        set_config("imaginary-config-file.yml")

        # execute
        result: str | None = get_base_image_name(self.DATASOURCE_NAME)

        # verify
        assert result is None 
        assert "Config is empty" in caplog.text
    
    def test_get_base_image_name_no_workspace(self):
        # setup
        set_config(self.CUSTOM_CONFIG_PATH)

        # execute
        result: str | None = get_base_image_name(self.DATASOURCE_NAME_NO_WORKSPACE)

        # verify
        assert result is None
    
    def test_get_base_image_name(self):
        # setup
        set_config(self.CUSTOM_CONFIG_PATH)

        # execute
        result: str | None = get_base_image_name(self.DATASOURCE_NAME)

        # verify
        assert result == "RGB"

    def test_get_base_image_path_no_config(self, caplog):
        # setup
        set_config("imaginary-config-file.yml")

        # execute
        result: str | None = get_base_image_path(self.DATASOURCE_NAME)

        # verify
        assert result is None 
        assert "Config is empty" in caplog.text
    
    def test_get_base_image_path_no_filepath(self):
        # setup
        set_config(self.CUSTOM_CONFIG_PATH)

        # execute
        result: str | None = get_base_image_path(self.DATASOURCE_NAME)

        # verify
        assert result is None
    
    def test_get_elemental_cube_path_from_name_no_config(self, caplog):
        # setup
        set_config("imaginary-config-file.yml")

        # execute
        result: str | None = get_elemental_cube_path_from_name(self.DATASOURCE_NAME, self.ELEMENTAL_CUBE_NAME)

        # verify
        assert result is None 
        assert "Config is empty" in caplog.text

    def test_get_elemental_cube_path_from_name_no_workspace(self):
        # setup
        set_config(self.CUSTOM_CONFIG_PATH)

        # execute
        result: str | None = get_elemental_cube_path_from_name(
            self.DATASOURCE_NAME_NO_WORKSPACE, self.ELEMENTAL_CUBE_NAME
        )

        # verify
        assert result is None
    
    def test_get_elemental_cube_path_from_name_invalid_name(self, caplog):
        # setup
        set_config(self.CUSTOM_CONFIG_PATH)
        cube_name: str = "not a cube"

        # execute
        result: str | None = get_elemental_cube_path_from_name(self.DATASOURCE_NAME, cube_name)

        # verify
        assert result is None
        assert f"Elemental cube with name {cube_name} not found in data source {self.DATASOURCE_NAME}" in caplog.text
