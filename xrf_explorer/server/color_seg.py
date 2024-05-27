import numpy as np
import cv2
from skimage import color
import skimage
import logging

LOG: logging.Logger = logging.getLogger(__name__)


def get_pixels_in_clusters(big_image: np.array, clusters: np.array, threshold: int = 10) -> np.array:
    """Assign each pixel from an image to a cluster based on a color similarity threshold using bitmasks.

    :param big_image: the image whose pixels are divided in clusters
    :param clusters: the clusters to which we add pixels
    :param threshold: the threshold that indicates how similar the colors need to are to be added to a cluster
       
    :return: the bitmasks corresponding to each cluster
    """

    bitmask: np.array = []

    # convert image to lab
    image: np.array = image_to_lab(big_image)

    # for each cluster
    for i in range(len(clusters)):
        # convert cluster color to lab
        target_color: int = rgb_to_lab(clusters[i])
        # define lower and upper bound for color similarity
        lower_bound: int = target_color - threshold
        upper_bound: int = target_color + threshold
        # append to bitmask the pixels with colors within the bounds
        bitmask.append(cv2.inRange(image, lower_bound, upper_bound))

    return bitmask


def merge_similar_colors(clusters: np.array, threshold: int = 10) -> np.array:
    """Go over every pair of clusters and merge the pair of they are similar according to threshold t.

    :param clusters: the currently available clusters
    :param threshold: the threshold that indicates how similar the colors need to are to be merged in a cluster
       
    :return: the new bitmask with potentially merged clusters and the new clusters
    """

    i: int = 0
    # Iterate over pairs of clusters
    while i < len(clusters):
        j: int = i + 1
        while j < len(clusters):
            # If two clusters are close, merge them
            if calculate_color_difference(clusters[i], clusters[j]) < threshold:
                # New cluster is average of the two
                new_color = (clusters[i] + clusters[j]) / 2
                # Remove old clusters, add new one
                clusters = np.delete(clusters, j, axis=0)
                clusters = np.delete(clusters, i, axis=0)
                clusters = np.append(clusters, [new_color], axis=0)
                j = i + 1
            else:
                j += 1
        i += 1
    return clusters


def get_clusters_using_k_means(image: np.array, small_image_size: int = 400, nr_of_attempts: int = 10, k: int = 30) -> tuple:
    """Extract the color clusters of the resized RGB image using the k-means clustering method in OpenCV

    :param image: the image to apply the k-means on
    :param small_image_size: size to resize given image to
    :param nr_of_attempts: the number of times the algorithm is executed using different initial labellings.
            Defaults to 20.
    :param k: number of clusters required at end. Defaults to 20.
       
    :return: an array of labels of the clusters and the array of centers of clusters
    """

    # set seed so results are consistent
    cv2.setRNGSeed(0)
    small_image = get_small_image(image, small_image_size)

    # reshape image
    reshaped_image: np.array = reshape_image(small_image)

    # criteria for stopping (stop the algorithm iteration if specified accuracy, eps, is reached or after max_iter
    # iterations.)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)

    # apply kmeans
    ret, label, center = cv2.kmeans(reshaped_image, k, None, criteria, nr_of_attempts, cv2.KMEANS_PP_CENTERS)

    return label, center


def image_to_lab(small_image: np.array) -> np.array:
    """
    Turns an image of RGB triples into an image of LAB triples.
    :param small_image: The scaled down version of the image.
    :return: The image in LAB format.
    """

    return color.rgb2lab(small_image)


def calculate_color_difference(lab1: np.array, lab2: np.array) -> int:
    """
    Returns the Euclidean distance between two LAB colors.
    :param lab1: color 1.
    :param lab2: color 2.
    :return: The distance.
    """

    return np.sqrt((lab1[0] - lab2[0]) ** 2 + (lab1[1] - lab2[1]) ** 2 + (lab1[2] - lab2[2]) ** 2)


def rgb_to_lab(rgb_triple: np.array) -> np.array:
    """
    Returns the LAB equivalent of an RGB color.
    :param rgb_triple: The RGB color triple.
    :return: the LAB format.
    """

    return skimage.color.rgb2lab([[[rgb_triple[0] / 255, rgb_triple[1] / 255, rgb_triple[2] / 255]]])[0][0]


def lab_to_rgb(lab_color: np.array) -> np.array:
    """
    Returns the RGB equivalent of an LAB color.
    :param lab_color: The LAB color triple.
    :return: The RGB color.
    """

    return skimage.color.lab2rgb([lab_color[0] / 255, lab_color[1] / 255, lab_color[2] / 255]) * 255


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


def reshape_image(small_image: np.array) -> np.array:
    """Reshape image into 2D array where each row represents a pixel and each pixel is
    represented as a 3-element array containing the RGB values

    :param small_image: the resized image to reshape
       
    :return: the reshaped image
    """

    return np.float32(small_image.reshape((-1, 3)))


def get_small_image(big_image: np.array, max_side_length: int = 300) -> np.array:
    """Resize a given image to fit within a maximum side length while preserving aspect ratio

    :param big_image: the image to be resized
    :param max_side_length: the maximum size of a side 
       
    :return: the resized image
    """

    # get height and width
    height: int = big_image.shape[0]
    width: int = big_image.shape[1]

    # Determine the scaling factor
    if height > width:
        scaling_factor: float = max_side_length / height
    else:
        scaling_factor: float = max_side_length / width

    # Calculate the new dimensions
    new_width: int = int(width * scaling_factor)
    new_height: int = int(height * scaling_factor)

    # Resize the image
    return cv2.resize(big_image, (new_width, new_height))


def get_image(image_file_path: str) -> np.array:
    """Read an image from the specified file path and convert it from BGR to RGB color space.

    :param image_file_path: the file path of the image
       
    :return: The image represented as a NumPy array in RGB color space.
    """

    try:
        raw_image: np.array = cv2.imread(image_file_path)
        if raw_image is None:
            raise FileNotFoundError(f"{image_file_path}")
        return cv2.cvtColor(raw_image, cv2.COLOR_BGR2RGB)
    except Exception as e:
        LOG.error(f"The path '{e}' is not a valid file path.")
        return None
