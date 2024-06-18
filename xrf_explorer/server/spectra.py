# This module contains all functions related to the spectral chart
import math
from os import makedirs
from os.path import join, isfile, isdir

import numpy as np
import xraydb
import logging
from math import ceil, floor

from xrf_explorer.server.file_system.file_access import get_raw_rpl_paths, get_spectra_params, parse_rpl, set_binned, \
    get_raw_rpl_names
from xrf_explorer.server.file_system.config_handler import get_config

LOG: logging.Logger = logging.getLogger(__name__)


def get_raw_data(data_source: str, level: int = 0) -> np.memmap | np.ndarray:
    """Parse the raw data cube of a data source as a 3-dimensional numpy array.

    :param data_source: the path to the .raw file.
    :param level: the mipmap level of the data to get.
    :return: memory map of the 3-dimensional array containing the raw data in format {x, y, channel}.
    """
    # get paths to files
    path_to_raw, path_to_rpl = get_raw_rpl_paths(data_source)

    # get dimensions from rpl file
    info = parse_rpl(path_to_rpl)
    if not info:
        return np.empty(0)
    width: int = ceil(int(info['width']) / (2 ** level))
    height: int = ceil(int(info['height']) / (2 ** level))

    # get mipmapped cube
    if level > 0:
        if not mipmap_exists(data_source, level):
            mipmap_raw_cube(data_source, level)
        config: dict = get_config()
        raw_name, _ = get_raw_rpl_names(data_source)
        path_to_raw: str = join(config["uploads-folder"], data_source, "generated", "mipmaps", str(level), raw_name)

    try:
        params: dict = get_spectra_params(data_source)
    except FileNotFoundError as err:
        LOG.error(
            "error while loading workspace to retrieve spectra params: {%s}", err)
        return np.array([])

    low: int = params["low"]
    high: int = params["high"]
    bin_size: int = params["binSize"]
    bin_nr: int = ceil((high-low)/bin_size)

    try:
        # load raw file and parse it as 3d array with correct dimensions
        datacube: np.memmap = np.memmap(path_to_raw, dtype=np.uint16, mode='r', shape=(height, width, bin_nr))
    except OSError as err:
        LOG.error("error while loading raw file: {%s}", err)
        return np.empty(0)
    return datacube


def mipmap_raw_cube(data_source: str, level: int):
    """Generates the mipmaps of the raw data in the data source up to the selected level.

    :param data_source: The data source to mipmap the data for.
    :param level: The level to mipmap the data to, 0 is original resolution
    """
    if level == 0:
        return

    if not mipmap_exists(data_source, level - 1):
        mipmap_raw_cube(data_source, level - 1)

    raw_name, _ = get_raw_rpl_names(data_source)

    LOG.info("Mipmapping spectral cube %s to level %i", raw_name, level)

    config: dict = get_config()
    mipmap_dir: str = join(config["uploads-folder"], data_source, "generated", "mipmaps", str(level))
    mipmap_path: str = join(mipmap_dir, raw_name)

    # Create directory for mipmap
    if not isdir(mipmap_dir):
        makedirs(mipmap_dir)

    # Get raw data from previous mipmap
    data: np.ndarray = get_raw_data(data_source, level - 1)

    mipmapped: np.memmap = np.memmap(
        mipmap_path,
        shape=(ceil(data.shape[0] / 2.0), ceil(data.shape[1] / 2.0), data.shape[2]),
        dtype=np.uint16,
        mode="w+"
    )

    for y in range(mipmapped.shape[0]):
        for x in range(mipmapped.shape[1]):
            mipmapped[y, x, :] = np.mean(data[2*y:2*y+2, 2*x:2*x+2, :], axis=(0, 1))

    # Write to disk
    mipmapped.flush()
    
    LOG.info("Finished mipmapping spectral cube %s to level %i", raw_name, level)


def mipmap_exists(data_source: str, level: int) -> bool:
    """Checks if a specific mipmap level exists for a data source.
    
    :param data_source: The datasource to check.
    :param level: The mipmap level to check.
    :return: Whether the specified mipmap level exists.
    """

    if level == 0:
        return True

    raw_name, _ = get_raw_rpl_names(data_source)

    config: dict = get_config()
    mipmap_path: str = join(config["uploads-folder"], data_source, "generated", "mipmaps", str(level), raw_name)

    return isfile(mipmap_path)


def bin_data(data_source: str, low: int, high: int, bin_size: int):
    """Reduces the raw data of a data source to channels in range [low:high] and averages channels per bin.

    :param data_source: the name of the data source containing the raw data.
    :param low: the lower channel boundary.
    :param high: the higher channel boundary.
    :param bin_size: the number of channels per bin.
    """
    # get paths to files
    path_to_raw: str
    path_to_rpl: str
    path_to_raw, path_to_rpl = get_raw_rpl_paths(data_source)

    # get dimensions from rpl file
    info = parse_rpl(path_to_rpl)
    if not info:
        return np.empty(0)
    # get dimensions of original data
    width: int = int(info['width'])
    height: int = int(info['height'])
    channels: int = int(info['depth'])

    # if default settings, don't do anything
    if low == 0 and high == 4096 and bin_size == 1:
        set_binned(data_source, True)
        return

    try:
        # load raw file and parse it as 3d array with correct dimensions
        datacube: np.ndarray = np.fromfile(path_to_raw, dtype=np.uint16)
    except OSError as err:
        LOG.error("error while loading raw file for binning: {%s}", err)
        raise
    datacube: np.ndarray = np.reshape(datacube, (height, width, channels))
    # if we just need to crop
    if bin_size == 1:
        new_cube: np.ndarray = datacube[:, :, low:high]
    else:
        # compute number of bins
        nr_bins: int = ceil((high-low)/bin_size)
        # initialize  array
        new_cube: np.ndarray = np.zeros(
            shape=(height, width, nr_bins), dtype=np.int16)

        for i in range(nr_bins):
            # convert bin number to start channel in original data (i.e. in range [0, 4096])
            start_channel = low + i*bin_size
            bin_average = np.mean(
                datacube[:, :, start_channel:start_channel+bin_size], axis=2)
            new_cube[:, :, i] = bin_average

    # overwrite file
    try:
        new_cube.flatten().tofile(path_to_raw)
    except Exception as e:
        LOG.error("Failed to write binned data: {%s}", e)
    set_binned(data_source, True)


def get_average_global(data: np.ndarray) -> list:
    """Computes the average of the raw data for each bin on the whole painting.

    :param data: datacube containing the raw data.
    :return: list with the average raw data for each channel in the range.
    """

    average_values: list = []

    mean: np.ndarray = np.mean(data, axis=(0, 1))

    # create list of dictionaries
    for i in range(np.size(mean)):
        average_values.append({"index": i, "value": mean[i]})

    return average_values


def get_average_selection(data_source: str, mask: np.ndarray) -> list:
    """Computes the average of the raw data for each bin on the selected pixels.

    :param data_source: name of the data source to get the selection average from.
    :param mask: The mask describing the selected pixels.
    :return: list with the average raw data for each bin in the range.
    """

    config: dict = get_config()
    max_points: int = int(config["max-spectrum-points"])

    num_points: int = np.count_nonzero(mask)
    level: int = 0
    if num_points > 0:
        level = max(0, ceil(math.log(num_points / max_points, 4)))

    LOG.info("Getting selection at mip level %i", level)

    data: np.ndarray = get_raw_data(data_source, level=level)
    length: int = data.shape[2]
    total: np.ndarray = np.zeros(length)

    scaled_mask: np.ndarray = np.empty((ceil(mask.shape[0] / 2**level), ceil(mask.shape[1] / 2**level)))
    scaled_mask.fill(False)

    indices: np.ndarray = np.argwhere(mask == True)

    # function to vectorize to set the map
    def set_mask(i: np.ndarray):
        nonlocal scaled_mask
        scaled_mask[floor(i[0] / 2**level), floor(i[1] / 2**level)] = True

    if indices.size > 0:
        np.vectorize(set_mask, signature="(2)->()")(indices)

    indices: np.ndarray = np.argwhere(scaled_mask == True)

    # Function to vectorize to calculate the average data
    def add_row(i: np.ndarray):
        nonlocal total
        total += data[i[0], i[1], :]

    average: np.ndarray = np.zeros(indices.shape[0])

    if indices.size > 0:
        np.vectorize(add_row, signature="(2)->()")(indices)
        average: np.ndarray = total / indices.shape[0]

    response: list = []

    # create list of dictionaries
    for i in range(np.size(average)):
        response.append({"index": i, "value": average[i]})

    LOG.info("Calculated the average spectrum for the selection.")
    return response


def get_theoretical_data(element: str, excitation_energy_kev: int, low: int, high: int, bin_size: int) -> list:
    """Get the theoretical spectrum and peaks of an element.
        Precondition: 0 <= low < high < 4096, 0 < bin_size <= 4096

        :param element: symbol of the element.
        :param excitation_energy_kev: excitation energy.
        :param low: lower channel boundary.
        :param high: higher channel boundary.
        :param bin_size: size of each bin.
        :return: list with first element being a list of dictionaries representing the spectra points, second being a list of dictionaries representing the peaks.
    """
    # remove last character to get periodic table symbol
    element = element[:len(element)-1].strip()
    if element == 'yAl':
        element = 'Al'

    try:
        # get spectrum and peaks
        data: tuple[np.ndarray, np.ndarray, np.ndarray,
                    np.ndarray] | np.ndarray = get_element_spectrum(element, excitation_energy_kev)
    except:
        LOG.info(f"Could not get theoretical spectral for excitation energy {excitation_energy_kev}")
        return []

    # get_element_spectrum returns normalized data, rescale to [0, 255]
    y_spectrum: np.ndarray = data[1]*255

    response: list = []

    spectrum: list = []
    bin_nr = ceil((high-low)/bin_size)

    # for each bin
    for i in range(bin_nr):
        # compute starting channel
        start_channel = low+i*bin_size

        # y_spectra has 10000 points instead of 4096, so scale index and bin size to slice it
        start_index = floor(start_channel*len(y_spectrum)/4096)
        new_bin_size = round(bin_size/((4096)/len(y_spectrum)))
        mean = np.mean(y_spectrum[start_index:start_index+new_bin_size])

        point = {"index": i, "value": mean}
        spectrum.append(point)

    response.append(spectrum)

    # get_element_spectrum returns data in domain [0, 40], rescale to [0, 4096]
    x_peaks = data[2]*4096/abs(data[0].max()-data[0].min())

    # get_element_spectrum returns normalized data, rescale to [0, 255]
    y_peaks = data[3]*255

    peaks = []
    for i in range(len(x_peaks)):
        # take only the peaks within the domain [low, high]
        if (low <= x_peaks[i] and high > x_peaks[i]):
            point = {"index": (x_peaks[i]-low)/bin_size, "value": y_peaks[i]}
            peaks.append(point)
    response.append(peaks)
    return response

# functions to compute theoretical elemental spectrum
# From xrf4u: https://github.com/fligt/maxrf4u/blob/main/maxrf4u/xphysics.py
# Author: Frank Ligterink


class ElementLines:
    """Computes fluorescence emission line energies and intensities for `element`.

    """

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


def get_element_spectrum(element: str, excitation_energy_kev: float, normalize: bool = True, x_kevs: np.ndarray | None = None, std: float = 0.01) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray] | np.ndarray:
    """Compute simple excitation spectrum (no matrix effects) and peaks

    :param element: symbol of the element
    :param excitation_energy_kev: excitation energy
    :param normalize: boolean representing whether to normalize y values
    :param x_kevs: pre-determined x values
    :param std: standard deviation of gaussian filter
    :return: x values of the spectrum, y values of the spectrum, peak energies, peak intensities
    """

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


def get_element_spectra(elements: list, x_kevs: np.ndarray, excitation_energy_kev: float) -> tuple[list, np.ndarray]:
    """Compute theoretical emission spectrum for multiple elements. 
    Sorts elements according to largest (alpha) peak. Based on xraydb. 

    :param elements: symbols of the elements
    :param x_kevs: pre-determined x values
    :param excitation_energy_kev: excitation energy
    :returns: elements, element_spectra
    """

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


def gaussian_convolve(peak_energies: np.ndarray, peak_intensities: np.ndarray, x_kevs: np.ndarray | None = None, std: float = 0.01) -> tuple[np.ndarray, np.ndarray]:
    """Convolves line spectrum defined by `peak_energies` and `peak_intensities` 
    with a Gaussian peak shape. 

    :param peak_energies: peak energies of the element
    :param peak_intensities: peak intensities of the element
    :param x_kevs: pre-determined x values
    :param std: standard deviation of gaussian filter
    """

    if x_kevs is None:
        x_kevs = np.linspace(0, 40, 10000)

    y_spectrum = np.zeros_like(x_kevs)

    for peak_energy, peak_intensity in zip(peak_energies, peak_intensities):

        y_spectrum += peak_intensity * \
            np.exp(-(1 / std) * (x_kevs - peak_energy)**2)

    return x_kevs, y_spectrum
