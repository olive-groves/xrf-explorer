"""
Service layer for datacube and greyscale stitching operations.
Handles the business logic for stitching requests.
"""
from __future__ import annotations

from logging import getLogger, Logger

import os
from os.path import join, exists
from pathlib import Path
from threading import Thread
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
from xrf_explorer.server.stitcher.transpose_state import (
    TransposeStateManager,
    TransposeState,
)

LOG: Logger = getLogger(__name__)

class FragmentData:
    """Represents fragment data and its associated properties.

    This class encapsulates data related to fragments, such as their source, cube type,
    rotation details, file paths, local points, and target points.

    Attributes:
        data_source (str): Name of the data source this fragment belongs to.
        cube_type (str): Specifies the type of the datacube (e.g., 'spectral', 'elemental').
        rotation (int): Rotation of the datacube fragment.
        datacube_filename (str): Name of the file storing the datacube.
        datacube_path (str): Full path to the datacube file within the data source from the project root directory.
        rpl_file (str | None): The RPL file path for spectral datacube fragments.
        fragment (DatacubeFragment): Object representing either a spectral or elemental
            datacube fragment.
        local_points (WarpSelection): Warp selection points containing coordinates on the fragment.
        target_points (WarpSelection): Warp selection points containing coordinates on the contextual image.
        points (tuple[WarpSelection, WarpSelection]): Tuple of local and target warp selection points.
    """
    data_source: str
    cube_type: str
    rotation: int
    datacube_filename: str
    datacube_path: str
    rpl_file: str | None
    fragment: DatacubeFragment
    local_points: WarpSelection
    target_points: WarpSelection
    points: tuple[WarpSelection, WarpSelection]

    def __init__(self, frag_data: Dict[str, Any], data_source: str, cube_type:str, target_dimensions: Dimensions):
        """
        Initializes a FragmentData object by processing fragment data, data source, and target dimensions.
        Verifies the type of datacube (spectral or elemental), sets up path and file
        reference, and establishes warp selections for local and target points.
        Verifies that the specified points are within valid bounds for both fragment and target dimensions.

        Args:
            frag_data (Dict[str, Any]): Input dictionary containing details about the fragment,
                such as the type, rotation, file references, and local/target points.
            data_source (str): Name of the data source this fragment belongs to.
            target_dimensions (Dimensions): Dimensions of the target (contextual image)

        Raises:
            ValueError: If local points are out of the fragment boundaries, or if target points
                fall outside the defined target dimensions.
        """
        # Assuming data is verified.
        self.data_source = data_source
        self.cube_type = cube_type
        self.rotation = frag_data["rotation"]
        self.datacube_filename = frag_data["datacube_file"]
        self.datacube_path = _build_path(frag_data.get("datacube_file"), data_source)

        # RPL File & Fragment
        if self.cube_type == "spectral":
            self.rpl_file = _build_path(frag_data.get("rpl_file"), data_source)

            self.fragment = SpectralDatacubeFragment.from_file(
                self.datacube_path, self.rpl_file, self.rotation
            )

        else:  # elemental
            self.rpl_file = None
            self.fragment = ElementalDatacubeFragment.from_file(self.datacube_path, self.rotation)

        # Local & Target points
        local_pts = frag_data["local_points"]
        target_pts = frag_data["target_points"]

        self.local_points = WarpSelection(
            top_left = local_pts["top_left"],
            top_right = local_pts["top_right"],
            bottom_left = local_pts["bottom_left"],
            bottom_right = local_pts["bottom_right"],
        )

        self.target_points = WarpSelection(
            top_left = target_pts["top_left"],
            top_right = target_pts["top_right"],
            bottom_left = target_pts["bottom_left"],
            bottom_right = target_pts["bottom_right"],
        )

        if not self.local_points.are_within(self.fragment.width, self.fragment.height):
            raise ValueError(f"Fragment '{self.datacube_path}' local points are out of bounds.")
        elif not self.target_points.are_within(target_dimensions.width, target_dimensions.height):
            raise ValueError(
                f"Fragment '{self.datacube_path}' target points are out of bounds."
            )

        self.points = (self.local_points, self.target_points)


class StitchData:
    """
    A class that encapsulates all data required for stitching operations.

    This class holds the necessary data and configuration for stitching datacubes,
    including contextual image information, fragment metadata, and alignment points.
    It serves as a data container and provides utility methods to access and process
    the stitching data.

    Attributes:
        data_source (str): Name of the data source this data belongs to.
        cube_type (str): The type of cube being processed ('spectral' or 'elemental').
        preview (bool): Indicates whether the stitching should be a preview or not (stitching on greyscale images vs. real data)
        scaling (int): User supplied factor applied to the optimal scalar for scaling contextual image that is being mapped to.
        contextual_image_name (str): Name of the contextual image.
        contextual_image_dimensions (Dimensions): Dimensions of the contextual image.
        points (list[tuple[WarpSelection, WarpSelection]]): List containing local and target points for all fragments.
        fragment_data (list[FragmentData]): Metadata for the individual datacube fragments.
    """
    data_source: str
    cube_type: str
    preview: bool
    scaling: int
    contextual_image_name: str
    contextual_image_dimensions: Dimensions
    points: list[tuple[WarpSelection, WarpSelection]]
    fragment_data: list[FragmentData]

    # Init
    def __init__(self, data: Dict[str, Any], data_source: str):
        """
        Initializes a StitchData object with provided data and data source and processes
        the data to extract relevant metadata and fragments.

        Assumes the input data is verified.

        Args:
            data (Dict[str, Any]): The validated JSON request data containing type,
                preview image, down scaling factor, contextual image name, and fragments.
            data_source (str): Name of the data source this data belongs to.

        Raises:
            KeyError: If the required keys are missing in the input data dictionary.

        """
        # Assuming data is verified.
        self.data_source = data_source
        self.cube_type = data["type"]
        self.preview = data["preview"]
        self.scaling = data["down_scaling"]
        self.contextual_image_name = data["contextual_image"]

        # Get contextual image dimensions
        self.get_contextual_image_dimensions()

        # Fragment data
        self.fragment_data = []
        for frag_data in data.get("fragments", []):
            self.fragment_data.append(FragmentData(frag_data, self.data_source, self.cube_type, self.contextual_image_dimensions))

        # Gather point tuples from all fragments

        self.points = []
        for fragment in self.fragment_data:
            self.points.append(fragment.points)

    def get_contextual_image_dimensions(self):
        """
        Gets the dimensions of a contextual image and sets them in the corresponding
        attribute. The method reads the image from the specified path, ensures it has
        valid dimensions, and handles errors if the image cannot be loaded or has
        invalid properties.

        Raises:
            FileNotFoundError: If the contextual image cannot be found or loaded.
            ValueError: If the loaded contextual image has invalid dimensions (e.g.,
                width or height equals zero).
        """
        # Contextual image dimensions
        image_path = _build_path(self.contextual_image_name, self.data_source)

        image = cv.imread(image_path, cv.IMREAD_GRAYSCALE)
        if image is None:
            raise FileNotFoundError(f"Failed to load contextual image: {image_path}")

        height, width = image.shape

        if width == 0 or height == 0:
            raise ValueError("Contextual image has invalid dimensions.")

        self.contextual_image_dimensions =  Dimensions(width, height)

    def get_fragments(self) -> list[DatacubeFragment]:
        """
        Returns a list of fragments extracted from the `fragment_data` attribute.

        Returns:
            list[DatacubeFragment]: A list of `DatacubeFragment` objects extracted
            from the `fragment_data` attribute.
        """
        return [frag.fragment for frag in self.fragment_data]

    def get_datacube_stitcher(self) -> DatacubeStitcher:
        """
        Creates and returns a DatacubeStitcher based on the configuration contained in the StitchData object.

        Returns:
            DatacubeStitcher: An initialized DatacubeStitcher instance.
        """
        output_dir = _build_path("", self.data_source)

        # Get scaling factor based on optimal scalar and user input
        optimizer = ScalarOptimizer(self.points)
        optimal_scalar, _ = optimizer.find_best_scalar()

        scalar = optimal_scalar * self.scaling

        # Create and return stitcher.
        return DatacubeStitcher(
            self.get_fragments(),
            self.points,
            self.contextual_image_dimensions,
            scalar,
            output_dir,
            data_source=self.data_source  # Pass data source for pre-transpose tracking
        )



def _build_path(path_value: str, data_source: str) -> str:
    """
    Generates a path to the file in the provided data source from the project root directory.

    Args:
        path_value: The user-supplied relative path.
        data_source: Name of the data source.

    Returns:
        Path to data source from project root.
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

def get_stitch_info(data: StitchData) -> Dict[str, Any]:
    """
    Calculates and retrieves stitch-related information based on input data.

    The function calculates the optimal scalar value for the provided configuration and calculates
    the expected file size of a stitched datacube with the given configuration.

    Args:
        data (StitchData): The stitch data object containing a stitching configuration.

    Returns:
        A dictionary containing:
            - optimal_scalar (float): The optimized scalar value computed from data points.
            - full_size (int): The calculated file size.
    """

    optimizer = ScalarOptimizer(data.points)
    optimal_scalar, _ = optimizer.find_best_scalar()
    reference_file_size = (
            data.get_fragments()[0].channels
            * data.contextual_image_dimensions.width
            * data.contextual_image_dimensions.height
    )
    return {"optimal_scalar": optimal_scalar, "full_size": reference_file_size}

def generate_partial_greyscale(frag_data: FragmentData) -> bool:
    """
    Generates a partial greyscale projection from a given fragment and exports it as an image file.
    This function creates a greyscale projection of the input fragment data, constructs the output
    directory, and saves the greyscale image as a PNG file.

    Args:
        frag_data: FragmentData object containing the fragment and metadata required to generate
            the greyscale projection.

    Returns:
        bool: True if the greyscale generation and export were successful; False otherwise.
    """
    try:
        fragment_greyscale = frag_data.fragment.create_greyscale_projection()

        output_dir = _build_path(join("generated", "stitching"), frag_data.data_source)
        os.makedirs(output_dir, exist_ok=True)

        export_path = join(output_dir, f"{frag_data.datacube_filename}.png")

        cv.imwrite(export_path, fragment_greyscale.astype(np.uint8))
    except FileNotFoundError as e:
        LOG.error(f"File not found while generating greyscale: {e}")
        return False
    except ValueError as e:
        LOG.error(f"Invalid value while generating greyscale: {e}")
        return False
    except cv.error as e:
        LOG.error(f"OpenCV error while generating greyscale: {e}")
        return False
    except Exception as e:
        LOG.error(f"Unexpected error while generating greyscale: {e}")
        return False

    return True


def generate_all_partial_greyscales(data: StitchData) -> bool:
    """
    Generates a partial greyscale projection for all fragments in the given stitch configuration
    and exports them as an image file.

    Args:
        data (StitchData): The stitch data object containing a stitching configuration.

    Returns:
        bool: True if the greyscale generation and export were successful for all fragments; False otherwise.
    """
    datasource_dir = _build_path(join("generated", "stitching"), data.data_source)

    all_conversions_successful = True

    for fragment_data in data.fragment_data:
        fragment_name = base_name = os.path.splitext(fragment_data.datacube_filename)[0]
        export_path = join(datasource_dir, f"{fragment_name}.png")

        # Generate greyscale if it does not exist yet
        if not exists(export_path):
            try:
                generate_partial_greyscale(fragment_data)
            except Exception as e:
                all_conversions_successful = False

    return all_conversions_successful


def get_fragment_greyscales(data: StitchData) -> List[np.ndarray]:
    """
    Retrieves the greyscales of fragments contained in the provided
    stitching configuration.
    If greyscale fragments do not already exist as image files, they are generated.

    Args:
        data (StitchData): The stitch data object containing a stitching configuration.

    Returns:
        List[np.ndarray]: A list of numpy arrays where each array contains the
            pixel data of a greyscale image corresponding to a fragment.
    """
    greyscales = []
    datasource_dir = _build_path(join("generated", "stitching"), data.data_source)

    for fragment_data in data.fragment_data:
        fragment_name = base_name = os.path.splitext(fragment_data.datacube_filename)[0]
        export_path = join(datasource_dir, f"{fragment_name}.png")

        # Generate greyscale if it does not exist yet
        if not exists(export_path):
            generate_partial_greyscale(fragment_data)

        greyscale_fragment = cv.imread(export_path)

        greyscales.append(greyscale_fragment)

    return greyscales

def stitch(data: StitchData) -> Dict[str, Any]:
    """
    Performs stitching operation based on the provided data.

    This function decides whether to perform greyscale stitching or a
    regular stitching operation based on the `preview` attribute
    of the given StitchData object.

    Args:
        data (StitchData): The data object containing stitching information
            and other relevant configurations.

    Returns:
        Dict[str, Any]: A dictionary containing the results of the stitching
            operation.
    """
    if data.preview:
        return stitch_greyscales(data)
    else:
        return perform_stitching(data)

def stitch_greyscales(data: StitchData) -> Dict[str, Any]:
    """
    Generates a stitched greyscale preview image.

    This function creates greyscale projections of the fragments, stitches them,
    normalizes the result, and saves a preview PNG.

    Args:
        data (StitchData): The stitch data object containing a stitching configuration.

    Returns:
        A dictionary containing the status, preview path, and image dimensions.
    """
    # Get greyscales
    preview_images = get_fragment_greyscales(data)

    # Get stitcher
    stitcher: DatacubeStitcher = data.get_datacube_stitcher()

    # Stitch greyscales
    result_image = stitcher.stitch_greyscales(preview_images)
    result_image = normalize_image(result_image)

    # Prepare output directory
    output_dir = _build_path(join("generated", "stitching"), data.data_source)
    os.makedirs(output_dir, exist_ok=True)

    # Save preview image
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

def perform_stitching(data: StitchData) -> Dict[str, Any]:
    """
    Performs full datacube stitching and recipe generation.

    This function stitches the datacube fragments, generates RPL/Recipe files,
    creates a greyscale projection of the final result, and saves the output.

    Args:
        data (StitchData): The stitch data object containing a stitching configuration.

    Returns:
        Dict[str, Any]: A dictionary containing the status of the stitching process, details
            about the output files, and metadata for the stitched result, including its type
            (spectral or elemental) and dimensions.

    Raises:
        OSError: If output directories cannot be created.
    """
    # Get stitcher
    stitcher: DatacubeStitcher = data.get_datacube_stitcher()

    # Full stitching
    result_fragment: DatacubeFragment = stitcher.stitch_datacubes()

    # Handle Spectral vs Elemental specific logic
    rpl_file = "stitched_spectral.rpl" if result_fragment.is_spectral else None

    recipe_path = result_fragment.create_recipe_file(
            _build_path("stitched_recipe.csv", data.data_source),
            Dimensions(result_fragment.width, result_fragment.height),
            data.contextual_image_dimensions
        )

    # Create projection for verification
    projection = result_fragment.create_greyscale_projection()
    projection = normalize_image(projection)

    # Save projection image
    output_dir = _build_path(join("generated", "stitching"), data.data_source)
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
            "channels": result_fragment.channels,
        },
    }

def validate_stitching_data(data: dict) -> tuple[bool, str]:
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

    is_spectral = data.get("type") == "spectral"

    if not isinstance(data.get("preview"), bool):
        return False, "preview must be boolean"

    if not isinstance(data.get("contextual_image"), str):
        return False, "contextual_image must be string"

    down_scaling = data.get("down_scaling")
    if not (isinstance(down_scaling, (int, float)) and 0 < down_scaling):
        return False, "down_scaling must be a number larger than 0"

    fragments = data.get("fragments")
    if not isinstance(fragments, list) or not fragments:
        return False, "fragments must be a non-empty list"

    for i, frag in enumerate(fragments):
        if not isinstance(frag, dict):
            return False, f"fragments[{i}] must be an object"

        for key in ("datacube_file", "rpl_file") if is_spectral else ["datacube_file"]:
            if not isinstance(frag.get(key), str):
                return False, f"fragments[{i}].{key} must be string"

        if frag.get("rotation") not in {0, 90, 180, 270}:
            return False, f"fragments[{i}].rotation must be one of: 0,90,180,270"

        for pts_key in ("local_points", "target_points"):
            pts = frag.get(pts_key)
            if not isinstance(pts, dict):
                return False, f"fragments[{i}].{pts_key} must be object"

            for corner in ("top_left", "top_right", "bottom_left", "bottom_right"):
                corner_val = pts.get(corner)
                if not isinstance(corner_val, (list, tuple)):
                    return False, f"fragments[{i}].{pts_key}.{corner} must be [x,y] array"

                # If it's a list/tuple, validate it has 2 integers
                if isinstance(corner_val, (list, tuple)):
                    if len(corner_val) != 2 or not all(isinstance(v, int) for v in corner_val):
                        return False, f"fragments[{i}].{pts_key}.{corner} must be [x, y] with integers"

    return True, ""

def _transpose_cube_worker(
    fragment: SpectralDatacubeFragment,
    data_source: str,
    cube_file: str,
    state_manager: TransposeStateManager
) -> None:
    """
    Worker function that performs the actual transpose operation in a background thread.
    
    Args:
        fragment: The spectral datacube fragment to transpose.
        data_source: Name of the data source.
        cube_file: Name of the cube file (for state tracking).
        state_manager: The TransposeStateManager instance.
    """
    try:
        # Perform the transpose - this creates a new transposed file
        transposed_fragment = fragment.create_transposed_version()
        
        # Mark as completed with the path to the transposed file
        state_manager.complete_transpose(
            data_source,
            cube_file,
            transposed_path=transposed_fragment.datacube_file
        )

    except Exception as e:
        LOG.error(f"Background transpose failed for {data_source}/{cube_file}: {e}")
        state_manager.complete_transpose(
            data_source,
            cube_file,
            error=str(e)
        )


def pre_transpose_cubes(data: StitchData) -> Dict[str, Any]:
    """
    Queues transpose operations for all spectral datacubes.
    
    This function adds transpose jobs to a queue for sequential processing.
    Only one transpose operation runs at a time to avoid overwhelming system resources.
    
    Args:
        data: The StitchData object containing fragment information.
        
    Returns:
        Dictionary containing:
            - status: "queued" or "no_action_needed"
            - message: Description of what was queued
            - cubes: List of cube files and their initial status
    """
    state_manager = TransposeStateManager.get_instance()
    
    cubes_queued = []
    cubes_skipped = []
    
    for fragment_data in data.fragment_data:
        cube_file = fragment_data.datacube_filename
        fragment = fragment_data.fragment
        
        # Only process spectral fragments
        if not isinstance(fragment, SpectralDatacubeFragment):
            LOG.info(f"Skipping non-spectral fragment: {cube_file}")
            cubes_skipped.append({
                "cube_file": cube_file,
                "reason": "not a spectral datacube"
            })
            continue
        
        # Check if already transposed (file exists)
        if fragment.is_transposed:
            LOG.info(f"Fragment already transposed: {cube_file}")
            cubes_skipped.append({
                "cube_file": cube_file,
                "reason": "already transposed"
            })
            continue
        
        # Create worker function for this specific fragment
        def create_worker(frag, ds, cf):
            """Closure to capture fragment, data_source, cube_file"""
            def worker():
                _transpose_cube_worker(frag, ds, cf, state_manager)
            return worker
        
        worker = create_worker(fragment, data.data_source, cube_file)
        
        # Try to enqueue transpose for this cube
        if state_manager.enqueue_transpose(data.data_source, cube_file, worker):
            cubes_queued.append({
                "cube_file": cube_file,
                "status": "queued"
            })
        else:
            # Already queued, in progress, or completed
            status = state_manager.get_status(data.data_source, cube_file)
            cubes_skipped.append({
                "cube_file": cube_file,
                "reason": f"already {status.status.value}"
            })
    
    return {
        "status": "queued" if cubes_queued else "no_action_needed",
        "message": f"Queued transpose for {len(cubes_queued)} cube(s), skipped {len(cubes_skipped)} cube(s)",
        "cubes_queued": cubes_queued,
        "cubes_skipped": cubes_skipped,
        "data_source": data.data_source
    }


def get_transpose_status(data_source: str) -> Dict[str, Any]:
    """
    Gets the current transpose status for all cubes in a data source.
    
    Args:
        data_source: Name of the data source.
        
    Returns:
        Dictionary containing:
            - data_source: The data source name
            - any_in_progress: Boolean indicating if any transposes are running
            - cubes: Dictionary mapping cube filenames to their status info
    """
    state_manager = TransposeStateManager.get_instance()
    
    statuses = state_manager.get_all_statuses(data_source)
    any_in_progress = state_manager.is_any_in_progress(data_source)
    
    # Convert TransposeInfo objects to dictionaries
    cubes_status = {
        cube_file: info.to_dict()
        for cube_file, info in statuses.items()
    }
    
    return {
        "data_source": data_source,
        "any_in_progress": any_in_progress,
        "cubes": cubes_status
    }