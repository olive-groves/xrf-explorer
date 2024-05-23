#This module contains all functions related to the spectral chart
from os.path import join
from pathlib import Path
import numpy as np 
import xraydb 
import logging

from xrf_explorer.server.file_system.config_handler import load_yml
LOG: logging.Logger = logging.getLogger(__name__)

def get_raw_data(raw_filename: str, rpl_filename: str, config_path: str = "config/backend.yml") -> np.ndarray:
    """Parse the raw data cube as a 3-dimensional numpy array
    
    :param raw_filename: the path to the .raw file
    :param rpl_filename: the path to the .rpl file
    :return: 3-dimensional array containing the raw data in format {x, y, channel}
    """
    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return np.empty(0)

    # get the path to the file in the server
    path_to_file: str = join(Path(backend_config['uploads-folder']), raw_filename)
    
    #get dimensions from rpl file
    info = parse_rpl(rpl_filename)
    width = int(info['width'])
    height = int(info['height'])
    channels = int(info['depth'])

    try:
        #load raw file and parse it as 3d array with correct dimensions
        datacube = np.memmap(path_to_file, dtype=np.uint16, mode='r')
    except OSError as err:
        LOG.error("error while loading raw file: {%s}", err)
        return []
    datacube = np.reshape(datacube, (width, height, channels))
    return datacube

def parse_rpl(filename, config_path: str = "config/backend.yml") -> dict:
    """Parse the given rpl file name as a dictionary, containing the following info:
        - width
        - height
        - depth
        - offset
        - data length
        - data type
        - byte order
        - record by
        
    :param filename: the path to the .rpl file
    :return: Dictionary containing the attributes' name and value
    """
    
    # load backend config
    backend_config: dict = load_yml(config_path)
    if not backend_config:  # config is empty
        LOG.error("Config is empty")
        return np.empty(0)

    # get the path to the file in the server
    path_to_file: str = join(Path(backend_config['uploads-folder']), filename)
    
    try:
        with open(path_to_file, 'r') as in_file:
            info = in_file.read().splitlines() #first split on linebreak
    except OSError as err:
        LOG.error("error while reading rpl file: {%s}", err)
        return {}
    
    map = {}
    if info:    
        for line in info:
            split = line.split("\t") #then split on tab
            map[split[0].strip()] = split[1].strip() #add tuple to dictionary
    else:
        LOG.error("Error while parsing rpl file: file empty")
               
    return map

def get_average_global(data: np.ndarray, low: int, high: int, bin_size: int) -> list:
    """Computes the average of the raw data for each bin of channels in range [low, high] on the whole painting
    Precondition: 0 <= low < high <= 4096, 0 < bin_sinze <= 4096
    
    :param data: datacube containing the raw data
    :param low: lower channel boundary
    :param high: higher channel boundary
    :param bin_size: size of each bin
    :return: list with the average raw data for each bin in the range
    """

    average_values = []
    
    #compute average per channel per bin size and add to dictionary
    for i in range(low, high, bin_size):
        mean = data[:, :, i:i+bin_size].mean()
        average_values.append({"index": i, "value": mean})
    
    return average_values

def get_average_selection(data: np.ndarray, pixels: np.ndarray, low: int, high: int, bin_size: int) -> list:
    """Computes the average of the raw data for each bin of channels in range [low, high] on the selected pixels
    Precondition: 0 <= low < high <= 4096, 0 < bin_sinze <= 4096
    Precondition: forall pixel in pixels, 0 <= pixel[0] < width, 0 <= pixel[1] < height
    
    :param data: datacube containing the raw data
    :param pixels: list of selected pixels
    :param low: lower channel boundary
    :param high: higher channel boundary
    :param bin_size: size of each bin
    :return: list with the average raw data for each bin in the range
    """
    
    if pixels:
        #initialize average array of length the number of channels
        sum = np.zeros(high-low)

        #add the required channels of all pixels
        for i in range(len(pixels)):
            pixel_data = data[pixels[i][0], pixels[i][1], low:high]
            sum = np.add(sum, pixel_data)
        
        #average
        avg = sum/len(pixels)
        
        result = []
        
        #average per bin
        for i in range(low, high, bin_size):
            mean = np.mean(avg[i-low:i-low+bin_size])
            dict = {"index": i, "value": mean}
            result.append(dict)   

        return result
    else :
        return []
    
def get_theoretical_data(element: str, excitation_energy_keV: int, low: int, high: int, bin_size: int) -> list:
    """Get the theoretical spectrum and peaks of an element
        Precondition: 0 <= low < high <= 4096, 0 < bin_sinze <= 4096

        :param element: symbol of the element
        :excitation_energy_keV: excitation energy
        :param low: lower channel boundary
        :param high: higher channel boundary
        :param bin_size: size of each bin
        :return: list with first element being a list of dictionaries representing the spectra points, secodn being a list of dictionaries representing the peaks
    """
    
    #remove last character to get periodic table symbol
    element = element[:len(element)-1]
    
    #get spectrum and peaks
    data = get_element_spectrum(element, excitation_energy_keV)
    
    #get_element_spectrum returns normalized data, rescale to [0, 255]
    y_scale = 255
    
    #get_element_spectrum returns 10000 points instead of 'high-low' points, so rescale bin_size
    bin_size = round(bin_size/((high-low)/len(data[0])))
    
    response = []
    spectrum = []
    for i in range(0, len(data[0]), bin_size):
        #take average of the y-values in the bin
        value = np.mean(data[1][i:i+bin_size])
        
        #rescale index to domain [low, high] and the mean to range [0, 255]
        dict = {"index": i*((high-low)/len(data[0]))+low, "value": value*y_scale}
        spectrum.append(dict)
    response.append(spectrum)
    
    #get_element_spectrum returns data in domain [0, 40], rescale to [low, high]
    x_scale = (high-low)/abs(data[0].max()-data[0].min())
    
    peaks = []
    for i in range(len(data[2])):
        #take only the peaks within the domain [high, low]
        if(low<=data[2][i]*x_scale + low and high > data[2][i]*x_scale + low):
            #scale x and y values
            dict = {"index": data[2][i]*x_scale + low, "value": data[3][i]*y_scale}
            peaks.append(dict)
    response.append(peaks)
    
    return response


#functions to compute theoratical elemental spectrum
#From xrf4u: https://github.com/fligt/maxrf4u/blob/main/maxrf4u/xphysics.py
#Author: Frank Ligterink
class ElementLines(): 
    '''Computes fluorescence emission line energies and intensities for `element`.
    
    '''
    
    def __init__(self, element, excitation_energy_keV): 

        excitation_energy = 1000 * excitation_energy_keV

        lines = xraydb.xray_lines(element, excitation_energy=excitation_energy) 

        peak_names = []
        peak_labels = []
        peak_energies = [] 
        peak_intensities = []

        for name, line in lines.items(): 

            peak_names.append(name)

            # intensities (a.k.a. transition probablities) sum up to unity within each level 
            energy, intensity, initial_level, final_level = line  
            peak_energies.append(energy)
            label = f'{element}_{initial_level}{final_level}' 
            peak_labels.append(label)

            # get corresponding edge properties 
            edge = initial_level # IUPAC notation!  e.g. 'L1', not 'La'
            edge_energy, fluo_yield, jump_ratio = xraydb.xray_edge(element, edge) 
            jump_coeff = (jump_ratio - 1) / jump_ratio # see Volker 
            #print(f'{name}: {energy}; jump_coeff: {jump_coeff:.03f}; fluo_yield: {fluo_yield}')

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

        
def get_element_spectrum(element, excitation_energy_keV, normalize=True, x_keVs=None, std=0.01): 
    '''Compute simple excitation spectrum (no matrix effects) and peaks
    
    :param element: symbol of the element
    :param excitation_energy_keV: excitation energy
    :param normalize: boolean representing wether to normalize y values
    :param x_keVs: pre-determined x values
    :param std: standard deviation of gaussian filter
    :return: x values of the spectrum, y values of the spectrum, peak energies, peak intensities
    '''
    
    el = ElementLines(element, excitation_energy_keV)  
    pe = el.peak_energies
    pi = el.peak_intensities
    
    x, y_spectrum = gaussian_convolve(pe, pi, x_keVs=x_keVs, std=std)
    
    if normalize: 
        y_spectrum = y_spectrum / y_spectrum.max()
        
    if x_keVs is None: 
    
        return x, y_spectrum, pe, pi
    
    else: 
        return y_spectrum

    
def get_element_spectra(elements, x_keVs, excitation_energy_keV): 
    '''Compute theoretical emission spectrum for multiple elements. 
    Sorts elements according to largest (alpha) peak. Based on xraydb. 
    
    :param element: symbols of the elements
    :param x_keVs: pre-determined x values
    :param excitation_energy_keV: excitation energy
    :returns: elements, element_spectra
    '''

    n_channels = len(x_keVs)
    n_elements = len(elements)

    element_spectra = np.zeros([n_elements, n_channels]) 

    for i, elem in enumerate(elements): 
        element_spectra[i] = get_element_spectrum(elem, excitation_energy_keV, x_keVs=x_keVs)

        # normalize
        element_spectra[i] = element_spectra[i] / element_spectra[i].max()


    # sort according to energy of largest (=alpha) peak
    alpha_idxs = np.argmax(element_spectra, axis=1)
    alpha_order = np.argsort(alpha_idxs) 

    elements = [elements[i] for i in alpha_order]
    element_spectra = element_spectra[alpha_order]
    
    return elements, element_spectra 

def gaussian_convolve(peak_energies, peak_intensities, x_keVs=None, std=0.01): 
    '''Convolves line spectrum defined by `peak_energies` and `peak_intensities` 
    with a Gaussian peak shape. 
    
    :param peak_energies: peak energies of the element
    :param peak_intensities: peak intensities of the element
    :param x_keVs: pre-determined x values
    :param std: standard deviation of gaussian filter
    '''
    
    if x_keVs is None: 
        x_keVs = np.linspace(0, 40, 10000)

    y_spectrum = np.zeros_like(x_keVs) 

    for peak_energy, peak_intensity in zip(peak_energies, peak_intensities): 

        y_spectrum += peak_intensity * np.exp(-(1 / std) * (x_keVs - peak_energy)**2)
        
    return x_keVs, y_spectrum 