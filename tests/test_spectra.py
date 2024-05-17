from xrf_explorer.server.spectra import *

class TestSpectra:
    rpl_path = 'C:/Users/20210792/Downloads/info.rpl'
    raw_path = 'C:/Users/20210792/Downloads/spectrum.raw'
    
    def test_get_average_global():
        data = np.ndarray([[[1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4]],
                           [[1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4]]])
        low = 1
        high = 3
        bin_size = 1
        result = get_average_global(data, low, high, bin_size)
        assert result == [{"index": 1, "value": 2}, {"index": 2, "value": 3}]