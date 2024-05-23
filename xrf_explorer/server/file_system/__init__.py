"""This module handles everything related to routing, storing, or extracting files in the backend of the application."""
from .elemental_cube import (
    normalize_elemental_cube, normalize_elemental_cube_per_layer, 
    get_elemental_data_cube, get_elemental_map,
    get_element_names, get_short_element_names, 
    get_element_averages
)