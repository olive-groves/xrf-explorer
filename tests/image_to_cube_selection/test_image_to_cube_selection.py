import numpy as np
from xrf_explorer.server.image_to_cube_selection import get_selected_data_cube


class TestImageToCubeSelection:
    PATH_DATA_SOURCE_DIR = "tests/resources/image_to_cube_selection"

    def test_get_selected_data_cube_dir_not_found(self, caplog):
        result: np.ndarray | None = get_selected_data_cube(
            "made/up/path", (0, 0), (1, 1)
        )

        assert result is None
        assert "Data source directory made/up/path does not exist." in caplog.text

    def test_get_selected_data_cube_dir_found(self):
        result: np.ndarray | None = get_selected_data_cube(
            self.PATH_DATA_SOURCE_DIR, (0, 0), (1, 1)
        )

        assert result is not None
