import numpy as np

from xrf_explorer.server.process.spectra import get_average_global


class TestSpectra:

    def test_get_average_global(self):
        data = np.array([[[1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4]],
                         [[1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4]]])

        result = get_average_global(data)
        expected_result = [{"index": 0, "value": 1.0},
                           {"index": 1, "value": 2.0},
                           {"index": 2, "value": 3.0},
                           {"index": 3, "value": 4.0}]
        assert result == expected_result

    def test_get_average_selection(self):
        data = np.array([[[3, 4, 3, 4], [1, 2, 3, 4], [2, 2, 3, 4],
                          [2, 0, 3, 4]]])

        result = get_average_global(data)
        expected_result = [{"index": 0, "value": 2.0},
                           {"index": 1, "value": 2.0},
                           {"index": 2, "value": 3.0},
                           {"index": 3, "value": 4.0}]
        assert result == expected_result
