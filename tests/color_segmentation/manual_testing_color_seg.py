import numpy as np

import matplotlib.pyplot as plt


def visualize_clusters(small_image: np.array, clusters: np.array):
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
