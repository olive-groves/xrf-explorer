import logging

import cv2
import numpy as np
import skimage
from os import path, makedirs
from skimage import color

from xrf_explorer.server.file_system import get_elemental_data_cube, normalize_elemental_cube_per_layer

LOG: logging.Logger = logging.getLogger(__name__)


def merge_similar_colors(clusters: np.ndarray, bitmasks: np.ndarray,
                         threshold: int = 7) -> tuple[np.ndarray, np.ndarray]:
    """Go over every pair of clusters and merge the pair of they are similar according to threshold t.

    :param clusters: the currently available clusters
    :param bitmasks: the bitmasks corresponding to the different clusters
    :param threshold: the threshold that indicates how similar the colors have to be in order
    to be merged in a cluster

    :return: the new bitmask with potentially merged clusters and the new clusters
    """

    LOG.info("Merging similar clusters.")
    # Transform colors to LAB format
    # (in LAB format, euclidean distance represent
    # similariy in color better)
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
    clusters = [lab_to_rgb(c).tolist() for c in clusters]
    # when doing rgb_to_lab and then lab_to_rgb the numbers
    # get slightly altered (e.g. 255->254.9), this fixes it
    clusters = np.array([[int(round(v)) for v in c] for c in clusters])

    return clusters, bitmasks


def get_clusters_using_k_means(image: np.ndarray, image_width: int = 100, image_height: int = 100,
                               nr_of_attempts: int = 10, k: int = 30) -> tuple[np.ndarray, np.ndarray]:
    """Extract the color clusters of the RGB image using the k-means clustering method in OpenCV

    :param image: the image to apply the k-means on
    :param image_width: the width to resize the image before applying k-means
    :param image_height: the height to resize the image before applying k-means
    :param nr_of_attempts: the number of times the algorithm is executed using different initial labellings.
            Defaults to 10.
    :param k: number of clusters required at end. Defaults to 30.

    :return: an array of labels of the clusters, the array of colors of clusters, and the array of bitmasks
    """
    # set seed so results are consistent
    cv2.setRNGSeed(0)

    # reshape image
    image: np.ndarray = cv2.resize(image, (image_width, image_height))
    reshaped_image: np.ndarray = reshape_image(image)

    # criteria for stopping (stop the algorithm iteration if specified accuracy, eps, is reached or after max_iter
    # iterations.)
    # At most 20 iterations and at least 1.0 accuracy
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)

    # apply kmeans
    colors: np.ndarray
    labels: np.ndarray
    _, labels, colors = cv2.kmeans(reshaped_image, k, np.empty(0), criteria, nr_of_attempts, cv2.KMEANS_PP_CENTERS)

    # Create bitmasks for each cluster
    bitmasks: list[list[bool]] = []
    for i in range(k):
        mask: np.ndarray = (labels == i)
        mask = mask.reshape(image.shape[:2])
        bitmasks.append(mask)

    LOG.info("Initial color clusters extracted successfully.")

    return np.array(colors), np.array(bitmasks)


def get_elemental_clusters_using_k_means(image: np.ndarray, data_cube_path: str,
                                         elem_threshold: float = 0.1,
                                         image_width: int = -1,
                                         image_height: int = -1,
                                         nr_of_attempts: int = 10, k: int = 30) -> tuple[np.ndarray, np.ndarray]:
    """Extract the color clusters of the RGB image per element using the k-means clustering method in OpenCV

    :param image: the image to apply the k-means on
    :param data_cube_path: the path to the data cube
    :param config_path: Path to the backend config file.
    :param elem_threshold: minimum concentration needed for an element to be present in the pixel
    :param image_width: the width to resize the image before applying k-means, if -1, the data cube's
                        dimensions are used instead
    :param image_height: the height to resize the image before applying k-means, if -1, the data cube's
                        dimensions are used instead
    :param nr_of_attempts: the number of times the algorithm is executed using different initial labellings.
                        Defaults to 10.
    :param k: number of clusters required at end. Defaults to 2.

    :return: a dictionary with an array of clusters and one with an array of bitmasks for each element
    """
    data_cube: np.ndarray = get_elemental_data_cube(data_cube_path)
    # Normalize the elemental data cube
    data_cube: np.ndarray = normalize_elemental_cube_per_layer(data_cube)

    # Generally we just register the image to the data cube
    if image_width == -1 or image_height == -1:
        dim = (data_cube.shape[2], data_cube.shape[1])
        # Rescale image to match data cube
        image = cv2.resize(image, dim)
    # Otherwise, we set the image and data cube to the given dimension
    else:
        image = cv2.resize(image, (image_width, image_height))
        target_dim = (image.shape[1], image.shape[0])
        data_cube = np.array([cv2.resize(img, target_dim) for img in data_cube])

    # set seed so results are consistent
    cv2.setRNGSeed(0)

    # criteria for stopping (stop the algorithm iteration if specified accuracy, eps, is reached or after max_iter
    # iterations.)
    # At most 20 iterations and at least 1.0 accuracy
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)

    colors: list[np.ndarray] = []
    bitmasks: list[list[np.ndarray]] = []
    # For each element
    for elem_index in range(data_cube.shape[0]):
        # Get bitmask of pixels with high element concentration
        # and get respective pixels in the image
        bitmask: np.ndarray = (data_cube[elem_index] >= elem_threshold).astype(bool)
        masked_image: np.ndarray = image[bitmask]
        masked_image = reshape_image(masked_image)

        # If empty image, continue (elem. not present)
        if masked_image.size == 0:
            colors.append(np.empty(0))
            bitmasks.append(np.empty(0))
            continue

        # k cannot be bigger than number of elements
        k = min(k, masked_image.size)
        labels: np.ndarray
        center: np.ndarray
        _, labels, center = cv2.kmeans(masked_image, k, np.empty(0), criteria, nr_of_attempts, cv2.KMEANS_PP_CENTERS)

        cluster_bitmasks: list[np.ndarray] = []
        labels = labels.flatten()
        subset_indices: np.ndarray = np.nonzero(bitmask)

        # For each cluster
        for i in range(k):
            # Indices for cluster "i"
            cluster_indices: np.ndarray = (labels == i)
            # Initialize empty mask
            cluster_mask: np.ndarray = np.zeros(image.shape[:2], dtype=bool)
            # Set values to true
            cluster_mask[subset_indices[0][cluster_indices], subset_indices[1][cluster_indices]] = True
            cluster_bitmasks.append(cluster_mask)

        colors.append(center)
        bitmasks.append(cluster_bitmasks)

    return colors, bitmasks


def combine_bitmasks(bitmasks: list[np.ndarray]) -> np.ndarray:
    """ Merges array of bitmasks into single bitmask with up to 32 bits = 4 bytes per entry,
    where the set bits determine the clusters that pixel corresponds to.

    :param bitmasks: the bitmasks corresponding to each cluster

    :return: a single bitmask in the form of an image (3 8bit entries per pixel) corresponding to
    the combination of all bitmasks
    """
    if len(bitmasks) == 0:
        return np.ndarray([])

    height, width = bitmasks[0].shape

    # Initialize the resulting image with 3 color channels
    combined_bitmask: np.ndarray = np.zeros((height, width), dtype=np.uint8)

    # i gives index, bitmask gives object at bitmasks[i]
    for i, bitmask in enumerate(bitmasks):
        # Bitmask i encoded w/value i+1 so it goes
        # in range [1, i+1]
        combined_bitmask[bitmask] = i + 1

    merged_image: np.ndarray = np.zeros((height, width, 3), dtype=np.uint8)
    merged_image[:, :, 0] = combined_bitmask

    return merged_image


def save_bitmask_as_png(bitmask: np.ndarray, full_path: str) -> bool:
    """ Saves the given bitmask as a png with the given name in the given path.

    :param bitmasks: the bitmask to be saved as png.
    :param full_path: the path (including image name) to save the file to.

    :return: true if the file was successfully saved, false otherwise.
    """
    try:
        # Ensure the directory exists
        dir_name = path.dirname(full_path)
        if not path.exists(dir_name):
            makedirs(dir_name)

        # Save the array as a PNG file using OpenCV
        success = cv2.imwrite(full_path, bitmask)
        if not success:
            raise IOError(f"Failed to save image to {full_path}")
            return False

        print(f"Image successfully saved to {full_path}")
        return True

    except Exception as e:
        print(f"An error occurred: {e}")

    return False


def calculate_color_difference(lab1: np.ndarray, lab2: np.ndarray) -> int:
    """
    Returns the Euclidean distance between two LAB colors.
    :param lab1: color 1.
    :param lab2: color 2.
    :return: The distance.
    """

    return np.linalg.norm(lab1 - lab2)


def image_to_lab(small_image: np.ndarray) -> np.ndarray:
    """
    Turns an image of RGB triples into an image of LAB triples.
    :param small_image: The scaled down version of the image.
    :return: The image in LAB format.
    """

    return color.rgb2lab(small_image)


def rgb_to_lab(rgb_triple: np.ndarray) -> np.ndarray:
    """
    Returns the LAB equivalent of an RGB color.
    :param rgb_triple: The RGB color triple.
    :return: the LAB format.
    """

    return skimage.color.rgb2lab([[[rgb_triple[0] / 255, rgb_triple[1] / 255, rgb_triple[2] / 255]]])[0][0]


def lab_to_rgb(lab_color: np.ndarray) -> np.ndarray:
    """
    Returns the RGB equivalent of an LAB color.
    :param lab_color: The LAB color triple.
    :return: The RGB color.
    """

    return skimage.color.lab2rgb([lab_color[0], lab_color[1], lab_color[2]]) * 255


def reshape_image(small_image: np.ndarray) -> np.ndarray:
    """Reshape image into 2D array where each row represents a pixel and each pixel is
    represented as a 3-element array containing the RGB values

    :param small_image: the resized image to reshape
    :return: the reshaped image
    """
    return np.float32(small_image.reshape((-1, 3)))


def get_image(image_file_path: str) -> np.ndarray:
    """Read an image from the specified file path and convert it from BGR to RGB color space.

    :param image_file_path: the file path of the image
    :return: The image represented as a NumPy array in RGB color space.
    """

    raw_image: np.ndarray = cv2.imread(image_file_path)
    try:
        raw_image: np.ndarray = cv2.cvtColor(raw_image,cv2.COLOR_BGR2RGB)
    except Exception as e:
        LOG.error(f"The path '{image_file_path}' is not a valid file path: {e}")
        return np.empty(0)

    if raw_image is None:
        LOG.error(f"The path '{image_file_path}' is not a valid file path.")
        return np.empty(0)
    return raw_image


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """
    Turns a rgb triple into hex format.
    :param r: the red value
    :param g: the green value
    :param b: the blue value
    :return: the hex format
    """

    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

def convert_to_hex(clusters: np.array) -> np.array:
    """
    Converts clusters to hex format.
    :param clusters: the list of clusters in rgb format
    :return: clusters in hex format
    """

    hex_clusters: np.array = []
    for col in clusters:
        hex_clusters.append(rgb_to_hex(int(col[0]), int(col[1]), int(col[2])))
    return hex_clusters
