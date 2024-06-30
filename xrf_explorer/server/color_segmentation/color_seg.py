import logging

from os import path, makedirs

import cv2
import numpy as np

from cv2.typing import MatLike
from skimage import color

from xrf_explorer.server.image_register import get_image_registered_to_data_cube
from xrf_explorer.server.file_system.cubes import normalize_elemental_cube_per_layer, get_elemental_data_cube

LOG: logging.Logger = logging.getLogger(__name__)


def merge_similar_colors(clusters: np.ndarray, bitmasks: np.ndarray,
                         threshold: int = 7) -> tuple[np.ndarray, np.ndarray]:
    """Go over every pair of clusters and merge the pair if they are similar according to the threshold.
    Currently unused function, left in code in case it becomes useful in the future.

    :param clusters: the currently available clusters
    :param bitmasks: the bitmasks corresponding to the different clusters
    :param threshold: the threshold that indicates how similar the colors have to be in order to be merged in a cluster
    :return: the new bitmask with potentially merged clusters and the new clusters
    """

    LOG.info("Merging similar clusters.")

    if clusters.size == 0 or bitmasks.size == 0:
        LOG.warning("Cluster or bitmask array length is zero")
        return np.empty(0), np.empty(0)

    # Transform colors to LAB format
    # (in LAB format, euclidean distance represent
    # similarity in color better)
    clusters = [rgb_to_lab(c) for c in clusters]

    i: int = 0
    # Iterate over pairs of clusters
    while i < len(clusters):
        j: int = i + 1
        while j < len(clusters):
            # If two clusters are close, merge them
            if calculate_color_difference(clusters[i], clusters[j]) < threshold:
                # New cluster is average of the two
                new_color: np.ndarray = (clusters[i] + clusters[j]) / 2
                # New bitmasks is bitwise OR
                new_bitmask: np.ndarray = np.bitwise_or(bitmasks[i], bitmasks[j])

                # Remove old clusters/bitmasks
                # Note that we remove j first since j > i
                clusters = np.delete(clusters, j, axis=0)
                clusters = np.delete(clusters, i, axis=0)
                bitmasks = np.delete(bitmasks, j, axis=0)
                bitmasks = np.delete(bitmasks, i, axis=0)
                # Add new clusters/bitmasks
                clusters = np.append(clusters, [new_color], axis=0)
                bitmasks = np.append(bitmasks, [new_bitmask], axis=0)
                j = i + 1
            else:
                j += 1
        i += 1

    LOG.info("Similar clusters merged successfully.")

    # Transform back to RGB
    clusters = np.array([lab_to_rgb(c).tolist() for c in clusters])

    return clusters, bitmasks


def get_clusters_using_k_means(data_source: str, image_name: str,
                               k: int = 30, nr_of_attempts: int = 10) -> tuple[np.ndarray, list[np.ndarray]]:
    """Extract the color clusters of the RGB image using the k-means clustering method in OpenCV

    :param data_source: the name of the data source
    :param image_name: the name of the image to apply k-means on
    :param k: number of clusters required at end. Defaults to 30
    :param nr_of_attempts: the number of times the algorithm is executed using different initial labellings. Defaults to 10
    :return: an array of labels of the clusters, the array of colors of clusters, and the array of bitmasks
    """
    # set seed so results are consistent
    cv2.setRNGSeed(0)
    LOG.info(f'Computing image-wide color clusters with parameters: k={k}, data_source={data_source}')

    # Get registered image
    registered_image: MatLike | None = get_image_registered_to_data_cube(data_source, image_name)
    if registered_image is None:
        LOG.error("Image could not be registered to data cube")
        return np.empty(0), []

    image: np.ndarray = cv2.cvtColor(registered_image, cv2.COLOR_BGR2RGB)
    reshaped_image: np.ndarray = reshape_image(image)

    # Transform image to LAB format
    reshaped_image = image_to_lab(reshaped_image)

    # criteria for stopping (stop the algorithm iteration if specified accuracy, eps, is reached or after max_iter
    # iterations.)
    # At most 50 iterations and at least 1.0 accuracy
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 1.0)

    # apply kmeans
    colors: np.ndarray
    labels: np.ndarray
    _, labels, colors = cv2.kmeans(reshaped_image, k, np.empty(0), criteria, nr_of_attempts, cv2.KMEANS_PP_CENTERS)
    labels = labels.reshape(image.shape[:2])

    # Create bitmasks for each cluster
    bitmasks: list[np.ndarray] = []
    for i in range(k):
        mask: np.ndarray = np.array(labels == i)
        bitmasks.append(mask)

    # Transform back to rgb
    colors = np.array([lab_to_rgb(c) for c in colors])
    LOG.info("Initial color clusters extracted successfully.")

    return colors, bitmasks


def get_elemental_clusters_using_k_means(data_source: str, image_name: str, elemental_channel: int,
                                         elem_threshold: float = 0.1, k: int = 30,
                                         nr_of_attempts: int = 10) -> tuple[np.ndarray, list[np.ndarray]]:
    """Extract the color clusters of the RGB image per element using the k-means clustering method in OpenCV

    :param data_source: the name of the data source
    :param image_name: the name of the image to apply k-means on
    :param elemental_channel: channel of the element to compute the color clusters of
    :param elem_threshold: minimum concentration needed for an element to be present in the pixel
    :param k: number of clusters required at end. Defaults to 30
    :param nr_of_attempts: the number of times the algorithm is executed using different initial labellings. Defaults to 10

    :return: a dictionary with an array of clusters and one with an array of bitmasks for each element
    """
    LOG.info(
        f'Computing element-wise color clusters with parameters:'
        f'k={k}, data_source={data_source}, elemental_channel={elemental_channel}'
    )

    # Get the elemental data cube
    data_cube: np.ndarray = get_elemental_data_cube(data_source)
    if data_cube.size == 0:
        LOG.error("Elemental data cube not found")
        return np.empty(0), []

    # Normalize the elemental data cube
    data_cube: np.ndarray = normalize_elemental_cube_per_layer(data_cube)

    # Get registered image
    registered_image: MatLike | None = get_image_registered_to_data_cube(data_source, image_name)
    if registered_image is None:
        LOG.error("Image could not be registered to data cube")
        return np.empty(0), []

    image: np.ndarray = cv2.cvtColor(registered_image, cv2.COLOR_BGR2RGB)

    # Transform image to lab
    image = image_to_lab(image)

    # set seed so results are consistent
    cv2.setRNGSeed(0)

    # criteria for stopping (stop the algorithm iteration if specified accuracy, eps, is reached or after max_iter
    # iterations.)
    # At most 50 iterations and at least 1.0 accuracy
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 1.0)

    # Get bitmask of pixels with high element concentration and get respective pixels in the image
    bitmask: np.ndarray = np.array(data_cube[elemental_channel] >= elem_threshold)
    masked_image: np.ndarray = image[bitmask]
    masked_image = reshape_image(masked_image)

    # If empty image, continue (elem. not present)
    if masked_image.size == 0:
        return np.empty(0), []

    # k cannot be bigger than number of pixels w/element present
    k = min(k, masked_image.size)
    labels: np.ndarray
    center: np.ndarray
    _, labels, center = cv2.kmeans(masked_image, k, np.empty(0), criteria, nr_of_attempts, cv2.KMEANS_PP_CENTERS)

    labels = labels.flatten()
    subset_indices: tuple[np.ndarray, ...] = np.nonzero(bitmask)

    bitmasks: list[np.ndarray] = []
    # Bitmasks for each cluster
    for i in range(k):
        # Indices for cluster "i"
        cluster_indices: np.ndarray = np.array(labels == i)
        # Initialize empty mask
        cluster_mask: np.ndarray = np.zeros(image.shape[:2])
        # Set values to true
        cluster_mask[subset_indices[0][cluster_indices], subset_indices[1][cluster_indices]] = True
        # Convert mask to boolean
        cluster_mask = cluster_mask.astype(bool)
        bitmasks.append(cluster_mask)

    # Transform back to rgb
    center = np.array([lab_to_rgb(c) for c in center])
    return center, bitmasks


def combine_bitmasks(bitmasks: list[np.ndarray]) -> np.ndarray:
    """Merges array of bitmasks into single bitmask, by setting the Green value of each pixel to store the index of
    the corresponding bitmask.

    :param bitmasks: the bitmasks corresponding to each cluster
    :return: a single bitmask in the form of an image corresponding to the combination of all bitmasks
    """
    if len(bitmasks) == 0:
        return np.empty(0)

    height, width = bitmasks[0].shape

    combined_bitmask: np.ndarray = np.zeros((height, width), dtype=np.uint8)

    # i gives index, bitmask gives object at bitmasks[i]
    for i, bitmask in enumerate(bitmasks):
        # Bitmask i encoded w/value i+1 so it goes
        # in range [1, i+1]
        combined_bitmask[bitmask] = i + 1

    # Initialize the resulting image with 3 color channels
    merged_image: np.ndarray = np.zeros((height, width, 3), dtype=np.uint8)
    # Store bitmask in Green channel
    merged_image[:, :, 1] = combined_bitmask

    return merged_image


def save_bitmask_as_png(bitmask: np.ndarray, full_path: str) -> bool:
    """Saves the given bitmask as a png with the given name in the given path.

    :param bitmask: the bitmask to be saved as png
    :param full_path: the path (including image name) to save the file to
    :return: true if the file was successfully saved, false otherwise
    """
    try:
        # Ensure the directory exists
        dir_name = path.dirname(full_path)
        if not path.exists(dir_name):
            makedirs(dir_name)

        # Save the array as a png file
        success = cv2.imwrite(full_path, bitmask)
        if not success:
            LOG.error(f"Failed to save image to {full_path}")
            return False

        LOG.info(f"Image successfully saved to {full_path}")
        return True

    except Exception as e:
        LOG.error(f"An error occurred: {e}")

    return False


def calculate_color_difference(lab1: np.ndarray, lab2: np.ndarray) -> int:
    """Returns the Euclidean distance between two LAB colors.

    :param lab1: color 1
    :param lab2: color 2
    :return: The distance
    """

    return np.linalg.norm(lab1 - lab2)


def image_to_lab(image: np.ndarray) -> np.ndarray:
    """Turns an image of RGB triples into an image of LAB triples.

    :param image: The image in RGB format (range: [0, 255])
    :return: The image in LAB format
    """

    return color.rgb2lab(image / 255)


def image_to_rgb(image: np.ndarray) -> np.ndarray:
    """Turns an image of LAB triples into an image of RGB triples.

    :param image: The image in LAB format (range: L = [0,100], AB = [-127,127])
    :return: The image in RGB format
    """

    rgb_image = color.lab2rgb(image) * 255
    # Round to the nearest integer and clip values to stay within valid range
    rgb_image = np.clip(np.round(rgb_image * 255), 0, 255).astype(np.uint8)
    return rgb_image


def rgb_to_lab(rgb_triple: np.ndarray) -> np.ndarray:
    """Returns the LAB equivalent of an RGB color.

    :param rgb_triple: The RGB color triple
    :return: the LAB format
    """

    return color.rgb2lab([[[rgb_triple[0] / 255, rgb_triple[1] / 255, rgb_triple[2] / 255]]])[0][0]


def lab_to_rgb(lab_color: np.ndarray) -> np.ndarray:
    """Returns the RGB equivalent of an LAB color.

    :param lab_color: The LAB color triple
    :return: The RGB color
    """
    rgb_color = color.lab2rgb([lab_color[0], lab_color[1], lab_color[2]]) * 255
    # when doing rgb_to_lab and then lab_to_rgb the numbers
    # get slightly altered (e.g. 255->254.9), this fixes it
    rgb_color = np.array([int(round(c)) for c in rgb_color])
    return rgb_color


def reshape_image(small_image: np.ndarray) -> np.ndarray:
    """Reshape image into 2D array where each row represents a pixel and each pixel is represented as a 3-element array
    containing the RGB values.

    :param small_image: the resized image to reshape
    :return: the reshaped image
    """
    return np.float32(small_image.reshape((-1, 3)))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Turns a rgb triple into hex format.

    :param r: the red value
    :param g: the green value
    :param b: the blue value
    :return: the hex format
    """

    return '#{:02x}{:02x}{:02x}'.format(r, g, b)


def convert_to_hex(clusters: np.ndarray) -> np.ndarray:
    """ Converts clusters to hex format.

    :param clusters: the list of clusters in rgb format
    :return: clusters in hex format
    """

    hex_clusters: np.ndarray = []
    for col in clusters:
        hex_clusters.append(rgb_to_hex(int(col[0]), int(col[1]), int(col[2])))
    return hex_clusters
