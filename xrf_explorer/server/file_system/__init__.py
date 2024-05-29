"""This module handles everything related to routing, storing, or extracting files in the backend of the application."""
from .elemental_cube import (
    normalize_ndarray_to_grayscale, normalize_elemental_cube_per_layer,
    get_elemental_data_cube, get_elemental_map,
    get_element_names, get_short_element_names,
    get_path_to_elemental_cube,
    get_element_averages, to_dms
)
from .from_dms import (
    get_elemental_datacube_dimensions_from_dms
)
from .workspace_handler import get_path_to_workspace, update_workspace
