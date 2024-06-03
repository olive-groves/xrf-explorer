import numpy as np

import sys

from os.path import join
from pathlib import Path

sys.path.append('.')

from xrf_explorer.server.file_system.config_handler import load_yml
from xrf_explorer.server.image_to_cube_selection import get_selected_data_cube

RESOURCES_PATH: Path = Path('tests', 'resources')

class TestImageToCubeSelection:
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, Path('configs', 'elemental-data.yml'))
    PATH_DATA_SOURCE_DIR = "tests/resources/image_to_cube_selection"

    def test_get_selected_data_cube_dir_not_found(self, caplog):
        # setup
        first: tuple[int, int] = (0, 0)
        second: tuple[int, int] = (1, 1)

        # load custom config
        custom_config: dict = load_yml(self.CUSTOM_CONFIG_PATH)
        path: str = join(Path(custom_config["uploads-folder"]), "made/up/path")
        expected_output: str = f"Data source directory {path} does not exist." 

        # execute
        result: np.ndarray | None = get_selected_data_cube(
            path, first, second
        )

        # verify
        assert result is None
        assert expected_output in caplog.text

    def test_get_selected_data_cube_dir_found(self):
        # setup
        first: tuple[int, int] = (0, 0)
        second: tuple[int, int] = (1, 1)
        path: str = join(RESOURCES_PATH, 'image_to_cube_selection')

        # result
        result: np.ndarray | None = get_selected_data_cube(
            path, first, second
        )

        # verify
        assert result is not None

    def test_get_selected_data_cube_dir_small(self):
        # setup
        first: tuple[int, int] = (0, 0)
        second: tuple[int, int] = (3, 5)
        path: str = join(RESOURCES_PATH, 'image_to_cube_selection')
        expected_result: np.ndarray = (<lo que esperas>)

        # result
        result: np.ndarray | None = get_selected_data_cube(
            path, first, second
        )

        # verify
        assert result == expected_result
