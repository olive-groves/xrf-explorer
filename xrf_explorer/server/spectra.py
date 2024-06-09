# This module contains all functions related to the spectral chart
import numpy as np
import xraydb
import logging
from math import ceil, floor

from xrf_explorer.server.file_system.file_access import get_raw_rpl_paths, get_spectra_params, parse_rpl
LOG: logging.Logger = logging.getLogger(__name__)


def get_raw_data(data_source: str) -> np.ndarray:
    """Parse the raw data cube of a data source as a 3-dimensional numpy array

    :param data_source: the path to the .raw file
    :return: 3-dimensional array containing the raw data in format {x, y, channel}
    """
    # get paths to files
    path_to_raw, path_to_rpl = get_raw_rpl_paths(data_source)

    # get dimensions from rpl file
    info = parse_rpl(path_to_rpl)
    if not info:
        return np.empty(0)
    width = int(info['width'])
    height = int(info['height'])

    try:
        params: dict = get_spectra_params(data_source)
    except FileNotFoundError as err:
        LOG.error(
            "error while loading workspace to retrieve spectra params: {%s}", err)
        return np.array([])

    low: int = params["low"]
    high: int = params["high"]
    bin_size: int = params["binSize"]
    bin_nr = ceil((high-low)/bin_size)

    try:
        # load raw file and parse it as 3d array with correct dimensions
        datacube = np.memmap(path_to_raw, dtype=np.uint16, mode='r')
    except OSError as err:
        LOG.error("error while loading raw file: {%s}", err)
        return np.empty(0)
    datacube = np.reshape(datacube, (height, width, bin_nr))
    return datacube


def bin_data(data_source: str, low: int, high: int, bin_size: int):
    """Reduces a the raw data of a data source to channels in range [low:high] and averages channels per bin.

    :param data_source: the name of the data source containing the raw data.
    :param low: the lower channel boundary.
    :param high: the higher channel boundary.
    :param bin_size: the number of channels per bin.
    """
    # get paths to files
    path_to_raw, path_to_rpl = get_raw_rpl_paths(data_source)

    # get dimensions from rpl file
    info = parse_rpl(path_to_rpl)
    if not info:
        return np.empty(0)
    # get dimensions of original data
    width = int(info['width'])
    height = int(info['height'])
    channels = int(info['depth'])

    try:
        # load raw file and parse it as 3d array with correct dimensions
        datacube = np.memmap(
            'C:/Users/20210792/Documents/GitHub/xrf-explorer/xrf_explorer/server/data/Painting/spectral.raw', dtype=np.uint16, mode='r')
    except OSError as err:
        LOG.error("error while loading raw file for binning: {%s}", err)
        raise
    datacube = np.reshape(datacube, (height, width, channels))

    nr_bins = ceil((high-low)/bin_size)

    # initialize  array
    new_cube = np.zeros(shape=(1187, 1069, nr_bins), dtype=np.int16)

    for i in range(nr_bins):
        # convert bin number to start channel in original data
        start_channel = low + i*bin_size

        bin = np.mean(
            datacube[:, :, start_channel:start_channel+bin_size], axis=2)
        new_cube[:, :, i] = bin

    # overwrite file
    new_cube.flatten().tofile(path_to_raw)


def get_average_global(data: np.ndarray) -> list:
    """Computes the average of the raw data for each bin on the whole painting

    :param data: datacube containing the raw data.
    :return: list with the average raw data for each channel in the range.
    """

    average_values = []

    mean = np.mean(data, axis=(0, 1))

    # create list of dictionaries
    for i in range(np.size(mean)):
        average_values.append({"index": i, "value": mean[i]})

    return average_values


def get_average_selection(data: np.ndarray) -> list:
    """Computes the average of the raw data for each bin on the selected pixels

    :param data: 2D array where the rows represent the selected pixels from the data cube image and the columns
    represent their energy channel value
    :return: list with the average raw data for each bin in the range
    """

    # compute average
    result = np.mean(data, axis=0)

    response = []

    # create list of dictionaries
    for i in range(np.size(result)):
        response.append({"index": i, "value": result[i]})

    return response


def get_theoretical_data(element: str, excitation_energy_kev: int, low: int, high: int, bin_size: int) -> list:
    """Get the theoretical spectrum and peaks of an element
        Precondition: 0 <= low < high < 4096, 0 < bin_size <= 4096

        :param element: symbol of the element
        :excitation_energy_kev: excitation energy
        :param low: lower channel boundary
        :param high: higher channel boundary
        :param bin_size: size of each bin
        :return: list with first element being a list of dictionaries representing the spectra points, second being a list of dictionaries representing the peaks
    """
    # remove last character to get periodic table symbol
    element = element[:len(element)-1]
    if element == 'yAl':
        element = 'Al'

    # get spectrum and peaks
    data = get_element_spectrum(element, excitation_energy_kev)

    # get_element_spectrum returns normalized data, rescale to [0, 255]
    y_spectrum = data[1]*255

    response = []

    spectrum = []
    bin_nr = ceil((high-low)/bin_size)

    # for each bin
    for i in range(bin_nr):
        # compute starting channel
        start_channel = low+i*bin_size

        # y_spectra has 10000 points instead of 4096, so scale index and bin size to slice it
        start_index = floor(start_channel*len(y_spectrum)/4096)
        new_bin_size = round(bin_size/((4096)/len(y_spectrum)))
        mean = np.mean(y_spectrum[start_index:start_index+new_bin_size])

        dict = {"index": i, "value": mean}
        spectrum.append(dict)

    response.append(spectrum)

    # get_element_spectrum returns data in domain [0, 40], rescale to [0, 4096]
    x_peaks = data[2]*4096/abs(data[0].max()-data[0].min())

    # get_element_spectrum returns normalized data, rescale to [0, 255]
    y_peaks = data[3]*255

    peaks = []
    for i in range(len(x_peaks)):
        # take only the peaks within the domain [low, high]
        if (low <= x_peaks[i] and high > x_peaks[i]):
            dict = {"index": (x_peaks[i]-low)/bin_size, "value": y_peaks[i]}
            peaks.append(dict)
    response.append(peaks)
    return response

# functions to compute theoretical elemental spectrum
# From xrf4u: https://github.com/fligt/maxrf4u/blob/main/maxrf4u/xphysics.py
# Author: Frank Ligterink


class ElementLines():
    '''Computes fluorescence emission line energies and intensities for `element`.

    '''

    def __init__(self, element, excitation_energy_kev):

        excitation_energy = 1000 * excitation_energy_kev

        lines = xraydb.xray_lines(element, excitation_energy=excitation_energy)

        peak_names = []
        peak_labels = []
        peak_energies = []
        peak_intensities = []

        for name, line in lines.items():

            peak_names.append(name)

            # intensities (a.k.a. transition probabilities) sum up to unity within each level
            energy, intensity, initial_level, final_level = line
            peak_energies.append(energy)
            label = f'{element}_{initial_level}{final_level}'
            peak_labels.append(label)

            # get corresponding edge properties
            edge = initial_level  # IUPAC notation!  e.g. 'L1', not 'La'
            edge_energy, fluo_yield, jump_ratio = xraydb.xray_edge(
                element, edge)
            jump_coeff = (jump_ratio - 1) / jump_ratio  # see Volker
            # print(f'{name}: {energy}; jump_coeff: {jump_coeff:.03f}; fluo_yield: {fluo_yield}')

            # multiplying edge jump coefficient, intensity and fluorescence yield...
            peak_intensity = jump_coeff * intensity * fluo_yield
            peak_intensities.append(peak_intensity)

        # determine sorting according to peak_intensities...
        self.peak_intensities = np.array(peak_intensities)
        indices = np.argsort(self.peak_intensities)[::-1]

        # sort
        self.peak_intensities = self.peak_intensities[indices]
        self.peak_energies = np.array(peak_energies)[indices] / 1000
        self.peak_names = np.array(peak_names)[indices]
        self.peak_labels = np.array(peak_labels)[indices]


def get_element_spectrum(element, excitation_energy_kev, normalize=True, x_kevs=None, std=0.01):
    '''Compute simple excitation spectrum (no matrix effects) and peaks

    :param element: symbol of the element
    :param excitation_energy_kev: excitation energy
    :param normalize: boolean representing wether to normalize y values
    :param x_kevs: pre-determined x values
    :param std: standard deviation of gaussian filter
    :return: x values of the spectrum, y values of the spectrum, peak energies, peak intensities
    '''

    el = ElementLines(element, excitation_energy_kev)
    pe = el.peak_energies
    pi = el.peak_intensities

    x, y_spectrum = gaussian_convolve(pe, pi, x_kevs=x_kevs, std=std)

    if normalize:
        y_spectrum = y_spectrum / y_spectrum.max()

    if x_kevs is None:

        return x, y_spectrum, pe, pi

    else:
        return y_spectrum


def get_element_spectra(elements, x_kevs, excitation_energy_kev):
    '''Compute theoretical emission spectrum for multiple elements. 
    Sorts elements according to largest (alpha) peak. Based on xraydb. 

    :param element: symbols of the elements
    :param x_kevs: pre-determined x values
    :param excitation_energy_kev: excitation energy
    :returns: elements, element_spectra
    '''

    n_channels = len(x_kevs)
    n_elements = len(elements)

    element_spectra = np.zeros([n_elements, n_channels])

    for i, elem in enumerate(elements):
        element_spectra[i] = get_element_spectrum(
            elem, excitation_energy_kev, x_kevs=x_kevs)

        # normalize
        element_spectra[i] = element_spectra[i] / element_spectra[i].max()

    # sort according to energy of largest (=alpha) peak
    alpha_idxs = np.argmax(element_spectra, axis=1)
    alpha_order = np.argsort(alpha_idxs)

    elements = [elements[i] for i in alpha_order]
    element_spectra = element_spectra[alpha_order]

    return elements, element_spectra


def gaussian_convolve(peak_energies, peak_intensities, x_kevs=None, std=0.01):
    '''Convolves line spectrum defined by `peak_energies` and `peak_intensities` 
    with a Gaussian peak shape. 

    :param peak_energies: peak energies of the element
    :param peak_intensities: peak intensities of the element
    :param x_kevs: pre-determined x values
    :param std: standard deviation of gaussian filter
    '''

    if x_kevs is None:
        x_kevs = np.linspace(0, 40, 10000)

    y_spectrum = np.zeros_like(x_kevs)

    for peak_energy, peak_intensity in zip(peak_energies, peak_intensities):

        y_spectrum += peak_intensity * \
            np.exp(-(1 / std) * (x_kevs - peak_energy)**2)

    return x_kevs, y_spectrum
