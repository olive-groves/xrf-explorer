import json

from logging import Logger, getLogger

import numpy as np

from flask import request

from xrf_explorer import app

from xrf_explorer.server.file_system.cubes import (
    get_spectra_params,
    update_bin_params,
    bin_data,
    parse_rpl,
    get_raw_data
)

from xrf_explorer.server.file_system.workspace import get_raw_rpl_paths
from xrf_explorer.server.image_to_cube_selection import CubeType
from xrf_explorer.server.routes.helper import encode_selection
from xrf_explorer.server.spectra import get_average_global, get_theoretical_data, get_average_selection

LOG: Logger = getLogger(__name__)


@app.route("/api/<data_source>/bin_raw/", methods=["POST"])
def bin_raw_data(data_source: str):
    """
    Bins the raw data files channels to compress the file.

    :param data_source: the data source containing the raw data to bin
    :return: A boolean indicating if the binning was successful
    """
    try:
        params: dict = get_spectra_params(data_source)
    except FileNotFoundError as err:
        return f"error while loading workspace to retrieve spectra params: {str(err)}", 500

    binned: bool = params["binned"]

    if not binned:
        try:
            update_bin_params(data_source)
            params: dict = get_spectra_params(data_source)
            low: int = params["low"]
            high: int = params["high"]
            bin_size: int = params["binSize"]

            bin_data(data_source, low, high, bin_size)
            LOG.info("binned")
            return "Binned data", 200

        except FileNotFoundError as err:
            return f"error while loading workspace to retrieve spectra params: {str(err)}", 5000
    else:
        return "Data already binned", 200


@app.route("/api/<data_source>/get_offset", methods=["GET"])
def get_offset(data_source: str):
    """
    Returns the depth offset energy of the raw data, that is the energy level of channel 0.

    :param data_source: the data source containing the raw data
    :return: The depth offset
    """
    _, path_to_rpl = get_raw_rpl_paths(data_source)

    # get dimensions from rpl file
    info = parse_rpl(path_to_rpl)
    if 'depthscaleorigin' not in info:
        return json.dumps(0)

    return json.dumps(float(info['depthscaleorigin']))


@app.route('/api/<data_source>/get_average_data', methods=['GET'])
def get_average_data(data_source: str):
    """
    Computes the average of the raw data for each bin of channels in range [low, high] on the whole painting.

    :return: json list of tuples containing the bin number and the average intensity for this bin
    """
    datacube: np.ndarray = get_raw_data(data_source)
    if len(datacube) == 0:
        return "Error occurred while getting raw data", 404

    average_values: list = get_average_global(datacube)

    return json.dumps(average_values)


@app.route('/api/<data_source>/get_element_spectrum/<element>/<excitation>', methods=['GET'])
def get_element_spectra(data_source: str, element: str, excitation: float):
    """
    Compute the theoretical spectrum in channel range [low, high] for an element with a bin size, as well as the
    element's peaks energies and intensity.

    :param data_source: the name of the data source, used for getting the spectrum boundaries and bin size
    :param element: the chemical element to get the theoretical spectra of
    :param excitation: the excitation energy
    :return: JSON list of tuples containing the bin number and the theoretical intensity for this bin, the peak energies
        and the peak intensities
    """
    try:
        params: dict[str, int] = get_spectra_params(data_source)
    except FileNotFoundError:
        return "error while loading workspace to retrieve spectra params: {%s}", 404

    if params is None:
        return "Error occurred while loading element spectrum", 404

    low: int = params["low"]
    high: int = params["high"]
    bin_size: int = params["binSize"]
    theoretical_data: list = get_theoretical_data(element, float(excitation), low, high, bin_size)

    return json.dumps(theoretical_data)


@app.route('/api/<data_source>/get_selection_spectrum', methods=['POST'])
def get_selection_spectra(data_source: str):
    """
    Get the average spectrum of the selected pixels of a rectangle selection.

    :param data_source: the name of the data source
    :return: JSON array where the index is the channel number and the value is the average intensity of that channel
    """
    mask: np.ndarray | None = encode_selection(request.get_json(), data_source, CubeType.Raw)
    if mask is None:
        return "Error occurred while getting selection from datacube", 500

    # get average
    result: list[float] = get_average_selection(data_source, mask)
    try:
        return json.dumps(result)
    except Exception as e:
        LOG.error(f"Failed to serialize element averages: {str(e)}")
        return "Error occurred while listing element averages", 500
