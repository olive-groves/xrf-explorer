"""This module handles everything related to routing, storing, or extracting files in the backend of the application."""
from .elemental_cube import (
    normalize_ndarray_to_grayscale, normalize_elemental_cube_per_layer,
    get_elemental_data_cube, get_elemental_map,
    get_element_names, get_short_element_names,
    get_element_averages, to_dms
)
from .workspace_handler import get_path_to_workspace, update_workspace
from .file_access import (
    get_elemental_cube_path_from_name, get_elemental_cube_path, get_base_image_name, get_elemental_cube_recipe_path
)
from .contextual_images import (
    get_contextual_image_path, get_contextual_image_recipe_path, 
    get_path_to_base_image, is_base_image, get_contextual_image_size
)
from .helper import set_config