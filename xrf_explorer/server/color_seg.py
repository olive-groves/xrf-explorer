import numpy as np
import time
import matplotlib.pyplot as plt
import cv2
from colormath.color_objects import LabColor, sRGBColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000
from sklearn.cluster import DBSCAN
from PIL import Image
from skimage import color
from matplotlib.colors import ListedColormap


def get_pixels_in_clusters(big_image, clusters):
    mask_images = {}
    cluster_images = {}

    for c in clusters: 
        target_color = np.array(c, dtype=np.uint8)
        lower_bound = np.clip(target_color - 20, 0, 255)
        upper_bound = np.clip(target_color + 20, 0, 255)
        mask = cv2.inRange(big_image, lower_bound, upper_bound)
        result = cv2.bitwise_and(big_image, big_image, mask=mask)
        mask_images[c] = mask 
        cluster_images[c] = result

    return (cluster_images, mask_images)

########################################################################################################################
# K-MEANS ##############################################################################################################
########################################################################################################################


def get_clusters_using_k_means(small_image, nr_of_attempts=20, k=-1):
    vectorized_image = get_image_as_vector(small_image)

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)

    if k == -1:
        k = get_optimal_k(small_image)

    ret, label, center = cv2.kmeans(vectorized_image, k, None, criteria, nr_of_attempts, cv2.KMEANS_PP_CENTERS)

    return label, center


def get_optimal_k(small_image):
    return 20


########################################################################################################################
# DBSCAN ###############################################################################################################
########################################################################################################################


def get_clusters_using_dbscan(small_image, eps=1.5, min_samples=20):
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

    #print(cluster_averages)
    return cluster_averages


def get_rgb_clusters_using_dbscan(clusters_as_lab):

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
    small_image = small_image.convert("RGB")
    width, height = small_image.size
    lab_colors = []
    for y in range(height):
        for x in range(width):
            # Get RGB color of pixel
            rgb_pixel = small_image.getpixel((x, y))
            # Convert RGB to Lab
            lab_color = rgb_to_lab(rgb_pixel)
            lab_colors.append(lab_color)
    return lab_colors


def find_closest_color_index(target_rgb, color_list):
    target_lab = rgb_to_lab(target_rgb)
    min_diff = float('inf')
    closest_index = -1

    for index, col in enumerate(color_list):
        lab = rgb_to_lab(col)
        diff = calculate_color_difference(target_lab, lab)
        if diff < min_diff:
            min_diff = diff
            closest_index = index

    return closest_index


def calculate_color_difference(lab1, lab2):
    color1 = LabColor(lab1[0], lab1[1], lab1[2])
    color2 = LabColor(lab2[0], lab2[1], lab2[2])
    return (lab1[0] - lab2[0])**2 + (lab1[1] - lab2[1])**2 + (lab1[2] - lab2[2])**2


def rgb_to_lab(rgb_triple):
    rgb_color = sRGBColor(rgb_triple[0] / 255, rgb_triple[1] / 255, rgb_triple[2] / 255)
    return convert_color(rgb_color, LabColor).get_value_tuple()


########################################################################################################################
# IMAGE FORMATTING #####################################################################################################
########################################################################################################################


def get_image_as_vector(small_image):
    return np.float32(small_image.reshape((-1, 3)))


def get_small_image(big_image, max_side_length=300):
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
    width, height = big_image.size

    if width > height:
        scale_factor = max_side_length / width
    else:
        scale_factor = max_side_length / height

    # Calculate the new dimensions
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)

    # Resize and save
    return big_image.resize((new_width, new_height))


def get_image(image_file_path):
    raw_image = cv2.imread(image_file_path)
    return cv2.cvtColor(raw_image, cv2.COLOR_BGR2RGB)


def get_image_as_pillow(image_file_path):
    return Image.open(image_file_path)


########################################################################################################################
# VISUALIZATION ########################################################################################################
########################################################################################################################

def visualize_image(image):
    plt.axis('off')
    plt.imshow(image)
    plt.title('Original Image')
    plt.show()


def visualize_segmented_image(small_image, clusters, label):
    clusters = np.uint8(clusters)
    res = clusters[label.flatten()]
    result_image = res.reshape(small_image.shape)

    figure_size = 15
    plt.figure(figsize=(figure_size, figure_size))
    plt.subplot(2, 3, 1), plt.imshow(small_image)
    plt.title('Original Image'), plt.xticks([]), plt.yticks([])
    plt.subplot(2, 3, 2), plt.imshow(result_image)
    plt.title('Segmented Image when K = %i' % len(clusters)), plt.xticks([]), plt.yticks([])
    plt.show()


def visualize_clusters(small_image, clusters):
    k = len(clusters)
    plt.figure()
    for i, col in enumerate(clusters):
        palette = np.zeros_like(small_image, dtype='uint8')
        palette[:, :, :] = col
        plt.subplot(1, k, i + 1)
        plt.axis("off")
        plt.imshow(palette)
    plt.show()


img_path = "/home/diego/Downloads/196_1989_RGB.tif"
img_pillow = get_image_as_pillow(img_path)
small_image_pillow = get_small_image_as_pillow(img_pillow, 200)
img = get_image(img_path)
small_image = get_small_image(img, 200)

start = time.time()

cluster = get_clusters_using_dbscan(small_image_pillow, eps=2, min_samples=30)
rgbClusters = get_rgb_clusters_using_dbscan(cluster)

cluster_res, mask_res = get_pixels_in_clusters(img, rgbClusters)

end = time.time()

print("Time taken: " + str(end - start))

for c in rgbClusters:
    # Create a colormap
    specific_color = [c[0]/255, c[1]/255, c[2]/255, 1]
    transparent = [1, 1, 1, 0]
    custom_cmap = ListedColormap([transparent, specific_color])

    ### Plots bitmask
    plt.subplot(1, 2, 1)
    plt.imshow(mask_res[c], cmap=custom_cmap)


    ### Plots image with bitmask applied to it
    plt.subplot(1, 2, 2)
    #plt.imshow(img)
    plt.imshow(cluster_res[c])

    plt.title(str(c), color = specific_color)
    plt.show()
