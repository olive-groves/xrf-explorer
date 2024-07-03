"""This module routes all incoming front-end requests to the appropriate backend functions"""

from .color_segmentation import get_color_clusters, get_color_cluster_bitmask
from .dim_reduction import get_dr_embedding, get_dr_overlay, get_dr_embedding_mapping
from .elemental_cube import (
    data_cube_size,
    data_cube_recipe,
    list_element_names,
    elemental_map,
    convert_elemental_cube,
    list_element_averages,
    list_element_averages_selection
)
from .general import api
from .images import contextual_image, contextual_image_size, contextual_image_recipe
from .project import (
    list_accessible_data_sources,
    datasource_files,
    get_workspace,
    create_data_source_dir,
    remove_data_source,
    delete_data_source,
    upload_chunk
)
from .spectral_cube import bin_raw_data, get_offset, get_average_data, get_element_spectra, get_selection_spectra
