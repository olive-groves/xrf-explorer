from xrf_explorer.server.spectra import *

class TestSpectra:
    rpl_path = 'C:/Users/20210792/Downloads/info.rpl'
    raw_path = 'C:/Users/20210792/Downloads/spectrum.raw'
    
    def test_get_average_global(self, caplog):
        data = np.array([[[1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4]],
                                                    [[1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4]]])
        low = 1
        high = 3
        bin_size = 1
        result = get_average_global(data, low, high, bin_size)
        expected_result = [{"index": 1, "value": 2}, {"index": 2, "value": 3}]
        assert result==expected_result
        
    def test_get_average_selection(self, caplog):
        data = np.array([[[3, 4, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4]],
                                                    [[1, 2, 3, 4], [1, 2, 1, 2], [1, 2, 3, 4]]])
        low = 1
        high = 3
        bin_size = 1
        pixels = [[0,0], [1,1]]
        result = get_average_selection(data, pixels, low, high, bin_size)
        expected_result = [{"index": 1, "value": 3}, {"index": 2, "value": 2}]
        assert result==expected_result