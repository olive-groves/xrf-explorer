"""
Service layer for datacube and greyscale stitching operations.
Handles the business logic for stitching requests.
"""
from __future__ import annotations

from logging import getLogger, Logger

import os
from os.path import join, exists
from pathlib import Path
from typing import Dict, Any, List

import cv2 as cv
import numpy as np
from matplotlib import pyplot as plt

from xrf_explorer.server.file_system import get_config

from xrf_explorer.server.stitcher.cube_fragments import (
    ElementalDatacubeFragment,
    SpectralDatacubeFragment,
    DatacubeFragment,
)
from xrf_explorer.server.stitcher.helper import (
    Dimensions,
    ScalarOptimizer,
    WarpSelection, normalize_image,
)
from xrf_explorer.server.stitcher.stitcher import DatacubeStitcher

LOG: Logger = getLogger(__name__)

def _build_path(path_value: str, data_source: str) -> str:
    """
    Converts a user-supplied relative path into an absolute one under uploads.

    Args:
        path_value: The user-supplied relative path.
        data_source: Name of the data source.

    Returns:
        Path to file from project root.
    Raises:
        ValueError: If backend configuration is missing."""

    backend_config: dict | None = get_config()
    if not backend_config:  # config is empty
        LOG.error("Backend configuration is empty")
        raise ValueError("Backend configuration is empty")

    if not exists(join(backend_config["uploads-folder"], data_source)):
        LOG.error(
            f"Data source folder at {join(backend_config['uploads-folder'], data_source)} does not exist.")
        raise ValueError(f"Data source folder at {join(backend_config['uploads-folder'], data_source)} does not exist.")

    return join(Path(backend_config["uploads-folder"]), data_source, path_value)


def load_contextual_image(image_name: str, data_source: str) -> tuple[np.ndarray, Dimensions]:
    """
    Loads the contextual image and returns it with its dimensions.
    Uses the base image from workspace if image_identifier is empty or "base".

    Args:
        image_identifier: The user-supplied relative path to the contextual image.
        data_source: Name of the data source.

    Returns:
        Tuple of (image, dimensions).

    Raises:
        FileNotFoundError: If image cannot be loaded.
    """
    if not image_name:
        raise ValueError("Contextual image identifier is empty")

    image_path = _build_path(image_name, data_source)
        
    image = cv.imread(image_path, cv.IMREAD_GRAYSCALE)
    if image is None:
        raise FileNotFoundError(f"Failed to load contextual image: {image_path}")

    height, width = image.shape
    return image, Dimensions(width, height)

def load_datacube_fragments(
    data: Dict[str, Any], data_source: str
) -> List[DatacubeFragment]:
    """
    Loads datacube fragments from the request data.

    Args:
        data: The validated JSON request data.
        data_source: Name of the data source.

    Returns:
        List of DatacubeFragment objects.

    Raises:
        FileNotFoundError: If any datacube file cannot be found.
    """
    fragments = []
    cube_type = data.get("type")

    for frag_data in data.get("fragments", []):
        rotation = frag_data["rotation"]
        datacube_file = _build_path(frag_data.get("datacube_file"), data_source)
        

        if cube_type == "spectral":
            rpl_file = _build_path(frag_data.get("rpl_file"), data_source)

            fragment = SpectralDatacubeFragment.from_file(
                datacube_file, rpl_file, rotation
            )
            
        else:  # elemental
            fragment = ElementalDatacubeFragment.from_file(datacube_file, rotation)

        fragments.append(fragment)

    return fragments

def get_stitch_info(data: Dict[str, Any], data_source: str) -> Dict[str, Any]:
    # Load contextual image
    _, dimensions = load_contextual_image(
        str(data.get("contextual_image")), data_source
    )

    # Load fragments
    fragments = load_datacube_fragments(data, data_source)

    # Parse warp points
    points = parse_warp_points(data)

    for i, points in enumerate(points):
        local_points, target_points = points
        fragment = fragments[0]
        if not local_points.are_within(fragment.width, fragment.height):
            raise ValueError(f"Fragment {i} local points are out of bounds.") # we should make errors json
        elif not target_points.are_within(dimensions.width, dimensions.height):
            raise ValueError(f"Fragment {i} target points are out of bounds.")

    if (dimensions.width == 0 or dimensions.height == 0):
        raise  ValueError("Contextual image has invalid dimensions.")

    optimizer = ScalarOptimizer(points)
    optimal_scalar, _ = optimizer.find_best_scalar()
    reference_file_size = fragments[0].channels * dimensions.width * dimensions.height
    return {
        "optimal_scalar": optimal_scalar,
        "full_size": reference_file_size
    }

def stitch_service(data: Dict[str, Any], data_source: str) -> Dict[str, Any]:
    """
    Performs datacube stitching based on the request data.

    Args:
        data: The validated JSON request data.
        data_source: The name of the data source.

    Returns:
        Dictionary with stitching results.

    Raises:
        FileNotFoundError: If required files cannot be found.
        ValueError: If datacubes are incompatible or parameters are invalid.
    """
    # Load contextual image
    _, dimensions = load_contextual_image(
        str(data.get("contextual_image")), data_source
    )

    # Load fragments
    fragments = load_datacube_fragments(data, data_source)

    # Parse warp points
    points = parse_warp_points(data)

    for i, points in enumerate(points):
        local_points, target_points = points
        fragment = fragments[0]
        if not local_points.are_within(fragment.width, fragment.height):
            raise ValueError(f"Fragment {i} local points are out of bounds.") # we should make errors json
        elif not target_points.are_within(dimensions.width, dimensions.height):
            raise ValueError(f"Fragment {i} target points are out of bounds.")

    if (dimensions.width == 0 or dimensions.height == 0):
        raise  ValueError("Contextual image has invalid dimensions.")

    # Get scaling factor
    scalar = data.get("scalar", 1.0)

    outputdir = _build_path("", data_source)

    # Create stitcher
    stitcher = DatacubeStitcher(
        fragments, points, dimensions, scalar, outputdir
    )

    # Perform stitching
    if data.get("preview", False):
        # Preview mode: only stitch greyscale projections
        preview_images = [frag.create_greyscale_projection() for frag in fragments]
        result_image = stitcher.stitch_greyscales(preview_images)
        result_image = normalize_image(result_image)
        
        # Save preview image
        output_dir = _build_path(join("generated", "stitching"),data_source)
        os.makedirs(output_dir, exist_ok=True)
        preview_path = join(output_dir, "preview.png")
        
        cv.imwrite(preview_path, result_image.astype(np.uint8))
        
        return {
            "status": "success",
            "preview": True,
            "preview_path": preview_path,
            "dimensions": {
                "width": int(stitcher.scaled_width),
                "height": int(stitcher.scaled_height),
            },
        }
    else:
        # Full stitching mode
        result_fragment = stitcher.stitch_datacubes()
        rpl_file = result_fragment.rpl_file if result_fragment.is_spectral else None
        if (result_fragment.is_spectral):
            recipe_path = result_fragment.create_recipe_file(_build_path("", "stitched_spectral_recipe.csv"))
        else: 
            recipe_path = result_fragment.create_recipe_file(_build_path("", "stitched_elemental_recipe.csv"))

        # raw = _build_path("stitched_spectral.raw",data_source)
        # rpl = _build_path("stitched_spectral.rpl",data_source)
        #
        # speccube = SpectralDatacubeFragment.from_file(raw,rpl)
        # projection = speccube.create_greyscale_projection()

        projection = result_fragment.create_greyscale_projection()
        projection = normalize_image(projection)
        
        # save projection image
        output_dir = _build_path(join("generated", "stitching"), data_source)
        os.makedirs(output_dir, exist_ok=True)
        projection_path = join(output_dir, "stitched_projection.png")
        cv.imwrite(projection_path, projection.astype(np.uint8))

        return {
            "status": "success",
            "preview": False,
            "output_file": result_fragment.datacube_file,
            "type": "spectral" if result_fragment.is_spectral else "elemental",
            "rpl_file": rpl_file,
            "recipe_file": recipe_path,
            "dimensions": {
                "width": result_fragment.width,
                "height": result_fragment.height,
                "channels": result_fragment.channels
            }
        }

def validate_stitching_request(data: dict) -> tuple[bool, str]:
    """
    Validates the stitching request payload.

    Args:
        data: The JSON request data.

    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is empty.
    """
    if data is None:
        return False, "Invalid or missing JSON"

    if data.get("type") not in ("elemental", "spectral"):
        return False, "type must be 'elemental' or 'spectral'"

    isSpectral = data.get("type") == "spectral"

    if not isinstance(data.get("preview"), bool):
        return False, "preview must be boolean"

    if not isinstance(data.get("contextual_image"), str):
        return False, "contextual_image must be string"

    down_scaling = data.get("down_scaling")
    if not (isinstance(down_scaling, (int, float)) and 0 < down_scaling <= 1):
        return False, "down_scaling must be a number in (0,1]"

    fragments = data.get("fragments")
    if not isinstance(fragments, list) or not fragments:
        return False, "fragments must be a non-empty list"

    for i, frag in enumerate(fragments):
        if not isinstance(frag, dict):
            return False, f"fragments[{i}] must be an object"

        for key in ("datacube_file", "rpl_file") if isSpectral else ["datacube_file"]:
            if not isinstance(frag.get(key), str):
                return False, f"fragments[{i}].{key} must be string"

        if frag.get("rotation") not in {0, 90, 180, 270}:
            return False, f"fragments[{i}].rotation must be 0,90,180,270"

        for pts_key in ("local_points", "target_points"):
            pts = frag.get(pts_key)
            if not isinstance(pts, dict):
                return False, f"fragments[{i}].{pts_key} must be object"

            for corner in ("top_left", "top_right", "bottom_left", "bottom_right"):
                corner_val = pts.get(corner)
                if not isinstance(corner_val, (int, list, tuple)):
                    return False, f"fragments[{i}].{pts_key}.{corner} must be int or [x,y] array"

                # If it's a list/tuple, validate it has 2 integers
                if isinstance(corner_val, (list, tuple)):
                    if len(corner_val) != 2 or not all(isinstance(v, int) for v in corner_val):
                        return False, f"fragments[{i}].{pts_key}.{corner} must be [x, y] with integers"

    return True, ""

def parse_warp_points(data: dict) -> list[tuple[WarpSelection, WarpSelection]]:
    """
    Parses warp selection points from the request data.

    Args:
        data: The validated JSON request data.

    Returns:
        List of tuples containing (local_points, target_points) as WarpSelection objects.
    """
    points = []

    for frag_data in data.get("fragments", []):
        local_pts = frag_data["local_points"]
        target_pts = frag_data["target_points"]

        local_selection = WarpSelection(
            top_left=tuple(local_pts["top_left"]),
            top_right=tuple(local_pts["top_right"]),
            bottom_left=tuple(local_pts["bottom_left"]),
            bottom_right=tuple(local_pts["bottom_right"]),
        )

        target_selection = WarpSelection(
            top_left=tuple(target_pts["top_left"]),
            top_right=tuple(target_pts["top_right"]),
            bottom_left=tuple(target_pts["bottom_left"]),
            bottom_right=tuple(target_pts["bottom_right"]),
        )

        points.append((local_selection, target_selection))

    return points