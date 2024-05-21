import numpy as np
import time
import matplotlib.pyplot as plt
import cv2
from sklearn.cluster import DBSCAN
from PIL import Image
from skimage import color
import skimage

def get_pixels_in_clusters(big_image, clusters, threshold):
    """Assign each pixel from an image to a cluster based on a color similarity threshold using bitmasks.

    :param big_image: the image whose pixels are divided in clusters
    :param clusters: the clusters to which we add pixels
    :param threshold: the threshold that indicates how similar the colors need to are to be added to a cluster
       
    :return: cluster images where each image contains pixels belonging to a specific color cluster and the bitmasks
    created
    """

    cluster_images = []
    bitmask = []

    # convert image to lab
    image = image_to_lab(big_image)

    # for each cluster
    for i in range(len(clusters)):
        # convert cluster color to lab
        target_color = rgb_to_lab(clusters[i])
        # define lower and upper bound for color similarity
        lower_bound = target_color - threshold 
        upper_bound = target_color + threshold
        # append to bitmask the pixels with colors within the bounds
        bitmask.append(cv2.inRange(image, lower_bound, upper_bound))
        # the pixels belonging to the color cluster
        cluster_images.append(cv2.bitwise_and(big_image, big_image, mask=bitmask[i]))

    return cluster_images, bitmask


def merge_similar_colors(clusters, t):
    """Assign each pixel from an image to a cluster based on a color similarity threshold using bitmasks

    :param bitmask: the bitmasks used for assigning pixels to clusters
    :param clusters: the currently available clusters
    :param t: the threshold that indicates how similar the colors need to are to be merged in a cluster
       
    :return: the new bitmask with potentially merged clusters and the new clusters
    """

    # for each cluster
    for i in range(len(clusters)):
        if i >= len(clusters):
            break

        # convert cluster color to lab
        col1 = rgb_to_lab(clusters[i])
        # compare to all the other clusters
        for j in range(len(clusters)):
            if j >= len(clusters):
                break
            # convert cluster color to lab
            col2 = rgb_to_lab(clusters[j])
            # if the color difference between two clusters is lower than the defined threshold
            if (calculate_color_difference(col1, col2) < t):
                # perform union of bitmasks
                # bitmask[i] = bitmask[j] | bitmask[i]

                # bitmask.pop(j)
                # set the new color of the cluster as the average between the colors of the two merged clusters
                clusters[i] = [np.sqrt((col1[0]**2+col2[0]**2)/2),np.sqrt((col1[1]**2+col2[1]**2)/2),np.sqrt((col1[2]**2+col2[2]**2)/2)]                # convert color if cluster back to rgb
                clusters[i] = lab_to_rgb(clusters[i])
                # delete one of the clusters
                clusters = np.delete(clusters, j, 0)
                if (j + 1) >= len(clusters) or (i + 1) >= len(clusters):
                    break
    return clusters


########################################################################################################################
# K-MEANS ##############################################################################################################
########################################################################################################################


def get_clusters_using_k_means(small_image, nr_of_attempts=20, k=20):
    """Extract the color clusters of the resized RGB image using the k-means clustering method in OpenCV

    :param small_image: the resized image to apply the k-means on
    :param nr_of_attempts: the number of times the algorithm is executed using different initial labellings. Defaults to 20.
    :param k: number of clusters required at end. Defaults to 20.
       
    :return: an array of labels of the clusters and the array of centers of clusters
    """

    #set seed so results are consistent
    cv2.setRNGSeed(0)

    # reshape image
    reshaped_image = reshape_image(small_image)

    # criteria for stopping (stop the algorithm iteration if specified accuracy, eps, is reached or after max_iter
    # iterations.)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)

    # apply kmeans
    ret, label, center = cv2.kmeans(reshaped_image, k, None, criteria, nr_of_attempts, cv2.KMEANS_PP_CENTERS)

    return label, center


########################################################################################################################
# DBSCAN ###############################################################################################################
########################################################################################################################


def get_clusters_using_dbscan(small_image, eps=1.5, min_samples=20):
    """
    Returns a list of LAB color triples corresponding to the color clusters. Found using DBSCAN.
    :param small_image: The scaled down version of the image.
    :param eps: A value to indicate the maximum distance between two colors to still be considered "similar".
    :param min_samples: The minimum number of neighbouring points required to be considered a core point.
    :return: The list of LAB color triples corresponding to the color clusters.
    """

    lab_colors = image_to_lab(small_image)
    data = np.array(lab_colors)

    # Initialize DBSCAN
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    # Fit the model and predict clusters
    labels = dbscan.fit_predict(data)

    # Get unique cluster labels excluding noise (-1)
    unique_labels = np.unique(labels[labels != -1])

    # Compute the average LAB color of each cluster
    cluster_averages = {}
    for unique_label in unique_labels:
        # Get indices of points belonging to the cluster
        cluster_indices = np.where(labels == unique_label)[0]
        # Get LAB colors of points in the cluster
        cluster_lab_colors = data[cluster_indices]
        # Compute the average LAB color of the cluster
        average_lab_color = np.mean(cluster_lab_colors, axis=0)
        cluster_averages[unique_label] = average_lab_color

    # print(cluster_averages)
    return cluster_averages


def get_rgb_clusters_using_dbscan(clusters_as_lab):
    """
    Returns a list of RGB color triples corresponding to the color clusters. Found using DBSCAN.
    :param clusters_as_lab: The clusters in LAB format.
    :return: The list of RGB color triples corresponding to the color clusters.
    """

    # Extract LAB color triples from the dictionary
    lab_colors = list(clusters_as_lab.values())

    # Convert the list of LAB colors to a NumPy array
    lab_array = np.array(lab_colors, dtype=np.float64)

    # Ensure the array is 3-dimensional with shape (1, N, 3) for skimage compatibility
    lab_array = lab_array[np.newaxis, :, :]

    # Convert the LAB array to an RGB array using skimage
    rgb_array = color.lab2rgb(lab_array)[0]

    # Scale the RGB values to the range [0, 255]
    rgb_array = (rgb_array * 255).astype(np.uint8)

    # Convert the RGB array back to a list of tuples
    rgb_colors = [tuple(rgb) for rgb in rgb_array]

    return rgb_colors


########################################################################################################################
# LAB METHODS ##########################################################################################################
########################################################################################################################

def image_to_lab(small_image):
    """
    Turns an image of RGB triples into an image of LAB triples.
    :param small_image: The scaled down version of the image.
    :return: The image in LAB format.
    """

    lab = color.rgb2lab(small_image)
    
    return lab


def calculate_color_difference(lab1, lab2):
    """
    Returns the Euclidean distance between two LAB colors.
    :param lab1: color 1.
    :param lab2: color 2.
    :return: The distance.
    """
    return np.sqrt((lab1[0] - lab2[0]) ** 2 + (lab1[1] - lab2[1]) ** 2 + (lab1[2] - lab2[2]) ** 2)


def rgb_to_lab(rgb_triple):
    """
    Returns the LAB equivalent of an RGB color.
    :param rgb_triple: The RGB color triple.
    :return: the LAB format.
    """
    return skimage.color.rgb2lab([[[rgb_triple[0] / 255, rgb_triple[1] / 255, rgb_triple[2] / 255]]])[0][0]
    


def lab_to_rgb(lab_color):
    """
    Returns the RGB equivalent of an LAB color.
    :param lab_color: The LAB color triple.
    :return: The RGB color.
    """
    return skimage.color.lab2rgb([lab_color[0] / 255, lab_color[1] / 255, lab_color[2] / 255])*255


########################################################################################################################
# IMAGE FORMATTING #####################################################################################################
########################################################################################################################


def reshape_image(small_image):
    """Reshape image into 2D array where each row represents a pixel and and each pixel is 
    represented as a 3-element array containing the RGB values

    :param small_image: the resized image to reshape
       
    :return: the reshaped image
    """
    return np.float32(small_image.reshape((-1, 3)))


def get_small_image(big_image, max_side_length=300):
    """Resize a given image to fit within a maximum side length while preserving aspect ratio

    :param big_image: the image to be resized
    :param max_side_length: the maximum size of a side 
       
    :return: the resized image
    """

    # get height and width
    height = big_image.shape[0]
    width = big_image.shape[1]

    # Determine the scaling factor
    if height > width:
        scaling_factor = max_side_length / height
    else:
        scaling_factor = max_side_length / width

    # Calculate the new dimensions
    new_width = int(width * scaling_factor)
    new_height = int(height * scaling_factor)

    # Resize the image
    return cv2.resize(big_image, (new_width, new_height))


def get_small_image_as_pillow(big_image, max_side_length=200):
    """Resize a given image to fit within a maximum side length while preserving aspect ratio

    :param big_image: the image to be resized
    :param max_side_length: the maximum size of a side 
       
    :return: the resized image
    """

    # get height and width
    width, height = big_image.size

    # Determine the scaling factor
    if width > height:
        scale_factor = max_side_length / width
    else:
        scale_factor = max_side_length / height

    # Calculate the new dimensions
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)

    # Resize 
    return big_image.resize((new_width, new_height))


def get_image(image_file_path):
    """Read an image from the specified file path and convert it from BGR to RGB color space.

    :param image_file path: the file path of the image
       
    :return: The image represented as a NumPy array in RGB color space.
    """
    raw_image = cv2.imread(image_file_path)
    return cv2.cvtColor(raw_image, cv2.COLOR_BGR2RGB)


def get_image_as_pillow(image_file_path):
    """Open image from the specified file path

    :param image_file path: the file path of the image
       
    :return: the loaded image as a Pillow Image object
    """

    return Image.open(image_file_path)


########################################################################################################################
# VISUALIZATION ########################################################################################################
########################################################################################################################


def visualize_clusters(small_image, clusters):
    """Visualize the color clusters of the resized image

    :param small_image: the resized image
    :param clusters: the list of clusters obtained
       
    :return: None
    """

    # the number of clusters
    k = len(clusters)
    plt.figure()

    # plotting the clusters
    for i, col in enumerate(clusters):
        palette = np.zeros_like(small_image, dtype='uint8')
        palette[:, :, :] = col
        plt.subplot(1, k, i + 1)
        plt.axis("off")
        plt.imshow(palette)
    plt.show()


def visualize_stacked_images(big_image, clusters, contrast):
    """Visualize the the image and highlighted colors while being able to adjust the contrast

    :param big_image: the original image
    :param clusters: the list of clusters obtained
    :param contrast: value that determines 
       
    :return: None
    """ 
    stacked_im = cv2.addWeighted(big_image, 1-contrast, clusters, 1, 0)
    stacked_image = Image.fromarray(stacked_im)
    plt.imshow(stacked_image)


### Get image(s)
img_path = "VGM_Package2024007_TUE_XrfExplorer2_Roulin_V20240424/196_1989_RGB.tif"
img_pillow = get_image_as_pillow(img_path)
small_image_pillow = get_small_image_as_pillow(img_pillow, 200)
img = get_image(img_path)
small_image = get_small_image(img, 400)

###
# Start timer
start = time.time()

k = 50
color_similarity_threshold = 6
color_merging_threshold = 1

# Get clusters
# cluster = get_clusters_using_dbscan(small_image_pillow, eps=2, min_samples=30)
# rgbClusters = get_rgb_clusters_using_dbscan(cluster)
label, rgbClusters = get_clusters_using_k_means(small_image, nr_of_attempts=20, k=k)

# merge similar clusters
newClusters = merge_similar_colors(rgbClusters, color_merging_threshold)

# map clusters with bitmask
cluster_res, bitmask = get_pixels_in_clusters(img, newClusters, color_similarity_threshold)



# End timer
end = time.time()
print("Time taken: " + str(end - start))
###

visualize_clusters(small_image, rgbClusters)
visualize_clusters(small_image, newClusters)

## Visualize clusters
# for c in rgbClusters:
for i in range(len(newClusters)):

    c = newClusters[i]
    # Create a colormap with cluster color
    specific_color = [c[0]/255, c[1]/255, c[2]/255, 1]

    # Plot 
    visualize_stacked_images(img, cluster_res[i], 0.8)
    plt.title(str(c), color = specific_color)
    plt.show()

