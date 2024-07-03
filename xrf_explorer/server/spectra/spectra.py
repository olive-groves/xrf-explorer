import logging

from math import ceil, floor, log

import numpy as np
import xraydb

from xrf_explorer.server.file_system import get_config
from xrf_explorer.server.file_system.cubes import get_raw_data

LOG: logging.Logger = logging.getLogger(__name__)


def get_average_global(data: np.ndarray) -> list[float]:
    """
    Computes the average of the raw data for each bin on the whole painting.

    :param data: datacube containing the raw data
    :return: list where the index is the channel number and the value is the average global intensity of that channel
    """

    mean: np.ndarray = np.mean(data, axis=(0, 1))

    return mean.tolist()


def get_average_selection(data_source: str, mask: np.ndarray) -> list[float]:
    """
    Computes the average of the raw data for each bin on the selected pixels.

    :param data_source: name of the data source to get the selection average from
    :param mask: The mask describing the selected pixels
    :return: list where the index is the channel number and the value is the average intensity of that channel within
        the selection
    """

    config: dict | None = get_config()
    if config is None:
        LOG.error("Could not get backend configuration")
        return []

    max_points: int = int(config["max-spectrum-points"])

    num_points: int = np.count_nonzero(mask)
    level: int = 0
    if num_points > 0:
        level = max(0, ceil(log(num_points / max_points, 4)))

    LOG.info("Getting selection at mip level %i", level)

    data: np.ndarray = get_raw_data(data_source, level=level)
    length: int = data.shape[2]
    total: np.ndarray = np.zeros(length)

    scaled_mask: np.ndarray = np.empty((ceil(mask.shape[0] / 2 ** level), ceil(mask.shape[1] / 2 ** level)))
    scaled_mask.fill(False)

    indices: np.ndarray = np.argwhere(mask)

    # function to vectorize to set the map
    def set_mask(index: np.ndarray):
        nonlocal scaled_mask
        scaled_mask[floor(index[0] / 2 ** level), floor(index[1] / 2 ** level)] = True

    if indices.size > 0:
        np.vectorize(set_mask, signature="(2)->()")(indices)

    indices: np.ndarray = np.argwhere(scaled_mask)

    # Function to vectorize to calculate the average data
    def add_row(index: np.ndarray):
        nonlocal total
        total += data[index[0], index[1], :]

    average: np.ndarray = np.zeros(indices.shape[0])

    if indices.size > 0:
        np.vectorize(add_row, signature="(2)->()")(indices)
        average: np.ndarray = total / indices.shape[0]

    LOG.info("Calculated the average spectrum for the selection.")
    return average.tolist()


def get_theoretical_data(element: str, excitation_energy_kev: float, low: int, high: int, bin_size: int) -> list:
    """
    Get the theoretical spectrum and peaks of an element.
    Precondition: 0 <= low < high < 4096, 0 < bin_size <= 4096, 0 <=excitation_energy_kev <= 40

    :param element: symbol of the element
    :param excitation_energy_kev: excitation energy
    :param low: lower channel boundary
    :param high: higher channel boundary
    :param bin_size: size of each bin
    :return: list with first element being a list of dictionaries representing the spectra points, second being a
        list of dictionaries representing the peaks
    """
    # remove last character to get periodic table symbol
    element = element[:len(element) - 1].strip()
    if element == 'yAl':
        element = 'Al'

    try:
        # get spectrum and peaks
        data: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray] | np.ndarray = (
            get_element_spectrum(element, excitation_energy_kev)
        )
    except:
        LOG.info(f"Could not get theoretical spectral for excitation energy {excitation_energy_kev}")
        return []

    # get_element_spectrum returns normalized data, rescale to [0, 255]
    y_spectrum: np.ndarray = data[1] * 255

    response: list = []

    spectrum: list = []
    bin_nr = ceil((high - low) / bin_size)

    # for each bin
    for i in range(bin_nr):
        # compute starting channel
        start_channel = low + i * bin_size

        # y_spectra has 10000 points instead of 4096, so scale index and bin size to slice it
        start_index = floor(start_channel * len(y_spectrum) / 4096)
        new_bin_size = round(bin_size / (4096 / len(y_spectrum)))
        mean = np.mean(y_spectrum[start_index:start_index + new_bin_size])
        spectrum.append(mean)

    response.append(spectrum)

    # get_element_spectrum returns data in domain [0, 40], rescale to [0, 4096]
    x_peaks = data[2] * 4096 / abs(data[0].max() - data[0].min())

    # get_element_spectrum returns normalized data, rescale to [0, 255]
    _ = data[3] * 255

    peaks = []
    for i in range(len(x_peaks)):
        # take only the peaks within the domain [low, high]
        if low <= x_peaks[i] < high:
            peaks.append((x_peaks[i] - low) / bin_size)
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
            _, fluo_yield, jump_ratio = xraydb.xray_edge(
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


def get_element_spectrum(
        element: str, excitation_energy_kev: float, normalize: bool = True,
        x_kevs: np.ndarray | None = None, std: float = 0.01
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray] | np.ndarray:
    """Compute simple excitation spectrum (no matrix effects) and peaks.

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

def gaussian_convolve(
        peak_energies: np.ndarray, peak_intensities: np.ndarray, x_kevs: np.ndarray | None = None, std: float = 0.01
) -> tuple[np.ndarray, np.ndarray]:
    """Convolve line spectrum defined by `peak_energies` and `peak_intensities` with a Gaussian peak shape.

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
                      np.exp(-(1 / std) * (x_kevs - peak_energy) ** 2)

    return x_kevs, y_spectrum
