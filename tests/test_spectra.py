from xrf_explorer.server.spectra import get_average_global, get_average_selection
import numpy as np


class TestSpectra:

    def test_get_average_global(self):
        # setup
        data: np.ndarray = np.array([[[1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4]],
                        [[1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4]]])
        expected_result: list[float] = [1.0, 2.0, 3.0, 4.0]

        # execute
        result: list[float] = get_average_global(data)

        # verify
        assert result == expected_result

    def test_get_average_selection(self):
        # setup
        data = np.array([[[3, 4, 3, 4], [1, 2, 3, 4], [2, 2, 3, 4],
                        [2, 0, 3, 4]]])
        expected_result: list[float] = [2.0, 2.0, 3.0, 4.0]

        # execute
        result: list[float ] = get_average_global(data)

        # verify
        assert result == expected_result
