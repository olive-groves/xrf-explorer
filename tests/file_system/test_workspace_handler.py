from logging import INFO

import sys

from os.path import join
from pathlib import Path

sys.path.append('.')

from xrf_explorer.server.file_system import get_workspace_path, update_workspace

RESOURCES_PATH: Path = Path('tests', 'resources')


class TestElementalData:
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, Path('configs', 'workspace_handler.yml'))
    WORKSPACE_NAME: str = "test_workspace"

    def test_config_not_found_workspace(self, caplog):
        # setup
        expected_output: str = "Failed to access config"

        # execute
        result: str = get_workspace_path(self.WORKSPACE_NAME, "imaginary-config-file.yml")
        
        # verify
        assert not result
        assert expected_output in caplog.text

    def test_workspace_not_found(self, caplog):
        # setup
        expected_output: str = "Workspace this_is_not_a_workspace not found."

        # execute
        result: str = get_workspace_path("this_is_not_a_workspace", self.CUSTOM_CONFIG_PATH)
        
        # verify
        assert not result
        assert expected_output in caplog.text

    def test_workspace_found(self, caplog):
        caplog.set_level(INFO)

        # setup
        expected_output: str = f"Workspace {self.WORKSPACE_NAME} found."

        # execute
        result: str = get_workspace_path(self.WORKSPACE_NAME, self.CUSTOM_CONFIG_PATH)
        
        # verify
        assert Path(RESOURCES_PATH, 'file_system', 'test_workspace', 'workspace.json').samefile(result)
        assert expected_output in caplog.text
