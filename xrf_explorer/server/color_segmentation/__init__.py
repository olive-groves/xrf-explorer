"""This module handles everything related to color segmentation."""

from .helper import get_path_to_cs_folder
from .color_seg import (
    combine_bitmasks, get_clusters_using_k_means,
    get_elemental_clusters_using_k_means, merge_similar_colors,
    save_bitmask_as_png, convert_to_hex
)
