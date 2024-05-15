import numpy as np
import matplotlib.pyplot as plt
import cv2
from colormath.color_objects import LabColor, sRGBColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000


def visualize_clusters(small_image, clusters):
    k = len(clusters)
    plt.figure()
    for i, color in enumerate(clusters):
        palette = np.zeros_like(small_image, dtype='uint8')
        palette[:, :, :] = color
        plt.subplot(1, k, i + 1)
        plt.axis("off")
        plt.imshow(palette)
    plt.show()


def get_pixels_in_clusters(big_image, clusters):
    pixels_in_clusters = [[] for _ in range(len(clusters))]
    for y in range(big_image.shape[0]):
        for x in range(big_image.shape[1]):
            i = find_closest_color_index(big_image[y][x], clusters)
            pixels_in_clusters[i].append((y, x))


def get_clusters_using_dbscan(small_image):
    return None


def get_clusters_using_k_means(small_image, nr_of_attempts=20, k=-1):
    vectorized_image = get_image_as_vector(small_image)

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)

    if k == -1:
        k = get_optimal_k(small_image)

    ret, label, center = cv2.kmeans(vectorized_image, k, None, criteria, nr_of_attempts, cv2.KMEANS_PP_CENTERS)

    return label, center


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


def get_optimal_k(small_image):
    return 20


def get_image_in_lab_format(rgb_image):
    lab_image = np.zeros_like(rgb_image, dtype=np.float64)

    for y in range(rgb_image.shape[0]):
        for x in range(rgb_image.shape[1]):
            lab_image[y, x, :] = rgb_to_lab(rgb_image[y, x, :])

    return lab_image


def find_closest_color_index(target_rgb, color_list):
    target_lab = rgb_to_lab(target_rgb)
    min_diff = float('inf')
    closest_index = -1

    for index, color in enumerate(color_list):
        lab = rgb_to_lab(color)
        diff = calculate_color_difference(target_lab, lab)
        if diff < min_diff:
            min_diff = diff
            closest_index = index

    return closest_index


def calculate_color_difference(lab1, lab2):
    color1 = LabColor(lab1[0], lab1[1], lab1[2])
    color2 = LabColor(lab2[0], lab2[1], lab2[2])
    return delta_e_cie2000(color1, color2)


def rgb_to_lab(rgb_triple):
    rgb_color = sRGBColor(rgb_triple[0] / 255, rgb_triple[1] / 255, rgb_triple[2] / 255)
    return convert_color(rgb_color, LabColor).get_value_tuple()


def get_image_as_vector(small_image):
    return np.float32(small_image.reshape((-1, 3)))


def get_small_image(big_image):
    return cv2.resize(big_image, None, fx=0.1, fy=0.1)  # TODO: Change to fixed size rather than percentage.


def visualize_image(image):
    plt.axis('off')
    plt.imshow(image)
    plt.title('Original Image')
    plt.show()


def get_image(image_file_path):
    raw_image = cv2.imread(image_file_path)
    return cv2.cvtColor(raw_image, cv2.COLOR_BGR2RGB)
