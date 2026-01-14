"""
Service layer for datacube and greyscale stitching operations.
Handles the business logic for stitching requests.
"""
from __future__ import annotations

from logging import getLogger, Logger

import os
from os.path import join, exists, basename
from pathlib import Path
from typing import Dict, Any, List

import cv2 as cv
import numpy as np

from xrf_explorer.server.file_system import get_config

from xrf_explorer.server.file_system.workspace import get_workspace_dict
from xrf_explorer.server.file_system.workspace.workspace_handler import update_workspace


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
)

LOG: Logger = getLogger(__name__)

class FragmentData:
    """Represents fragment data and its associated properties.

    This class encapsulates data related to fragments, such as their source, cube type,
    rotation details, file paths, local points, and target points.

    Attributes:
        data_source (str): Name of the data source this fragment belongs to.
        cube_type (str): Specifies the type of the datacube (e.g., 'spectral', 'elemental').
        _rotation (int): Rotation of the datacube fragment.
        datacube_filename (str): Name of the file storing the datacube.
        datacube_path (str): Full path to the datacube file within the data source from the project root directory.
        _rpl_file (str | None): The RPL file path for spectral datacube fragments.
        _fragment (DatacubeFragment): Object representing either a spectral or elemental
            datacube fragment.
        _local_points (WarpSelection): Warp selection points containing coordinates on the fragment.
        _target_points (WarpSelection): Warp selection points containing coordinates on the contextual image.
        _points (tuple[WarpSelection, WarpSelection]): Tuple of local and target warp selection points.
    """

    data_source: str
    cube_type: str
    datacube_filename: str
    datacube_path: str

    _rotation: int | None
    _rpl_file: str | None
    _fragment: DatacubeFragment | None
    _local_points: WarpSelection | None
    _target_points: WarpSelection | None
    _points: tuple[WarpSelection, WarpSelection] | None

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
        self.data_source = data_source
        self.cube_type = cube_type

        # Verify datacube file and rpl file (Mandatory)
        is_spectral = cube_type == "spectral"

        for key in ("datacube_file", "rpl_file") if is_spectral else ["datacube_file"]:
            if not isinstance(frag_data.get(key), str):
                raise ValueError(f"fragments[].{key} must be string")

        self.datacube_filename = frag_data["datacube_file"]
        self.datacube_path = _build_path(frag_data["datacube_file"], data_source)
        self._rpl_file = _build_path(frag_data["rpl_file"], data_source) if is_spectral else None

        # Fragment
        if is_spectral:
            self._fragment = SpectralDatacubeFragment.from_file(
                self.datacube_path, self._rpl_file, frag_data.get("rotation", 0)
            )
        else:  # elemental
            self._fragment = ElementalDatacubeFragment.from_file(
                self.datacube_path, frag_data.get("rotation", 0)
            )

        # Rotation
        rotation = frag_data.get("rotation", 0)

        if rotation not in {0, 90, 180, 270}:
            raise ValueError(
                f"fragment {self.datacube_filename}, rotation must be one of: 0,90,180,270"
            )

        self._rotation = rotation

        # Points validation
        for pts_key in ("local_points", "target_points"):
            pts = frag_data.get(pts_key)
            if not isinstance(pts, dict | None):
                raise ValueError(
                    f"fragment {self.datacube_filename}, {pts_key} must be dictionary"
                )

            # If one of the points is not present, set variables to None and stop validating.
            if pts is None:
                self._local_points = None
                self._target_points = None
                break

            for corner in ("top_left", "top_right", "bottom_left", "bottom_right"):
                corner_val = pts.get(corner)
                if not isinstance(corner_val, (list, tuple)):
                    raise ValueError(
                        f"fragment {self.datacube_filename}, {pts_key}.{corner} must be [x,y] array"
                    )

                # If it's a list/tuple, validate it has 2 integers
                if isinstance(corner_val, (list, tuple)):
                    if len(corner_val) != 2 or not all(
                        isinstance(v, int | float) for v in corner_val
                    ):
                        raise ValueError(
                            f"fragment {self.datacube_filename}, {pts_key}.{corner} must be [x, y] with integers"
                        )

            # Setting validated points
            if pts_key == "local_points":
                self._local_points = WarpSelection(
                    pts["top_left"],
                    pts["top_right"],
                    pts["bottom_left"],
                    pts["bottom_right"],
                    self.fragment.rotated_height
                )
            else:
                self._target_points = WarpSelection(
                    pts["top_left"],
                    pts["top_right"],
                    pts["bottom_left"],
                    pts["bottom_right"],
                    target_dimensions.height
                )

        # Verify points are within boundaries
        if self._local_points and self._target_points:
            if not self._local_points.are_within(
                self._fragment.rotated_width, self._fragment.rotated_height
            ):
                raise ValueError(
                    f"Fragment local points are out of bounds."
                    f"Fragment rotated dimensions: {self._fragment.rotated_width}x{self._fragment.rotated_height}"
                    f"Local points: {self._local_points}"
                )
            elif not self._target_points.are_within(
                target_dimensions.width, target_dimensions.height
            ):
                raise ValueError(
                    f"Fragment target points are out of bounds."
                )

        self._points = (self._local_points, self._target_points)

    @property
    def rotation(self) -> int:
        """
        Property that returns the rotation of the fragment.

        Returns:
            int: The rotation value (0, 90, 180, or 270).

        Raises:
            ValueError: If rotation is not set.
        """
        if self._rotation is not None:
            return self._rotation
        else:
            raise ValueError("'rotation' requested but not present in fragment data.")

    @property
    def rpl_file(self) -> str:
        """
        Property that returns the RPL file path.

        Returns:
            str: The RPL file path.

        Raises:
            ValueError: If rpl_file is not set (e.g., for elemental cubes).
        """
        if self._rpl_file is not None:
            return self._rpl_file
        else:
            raise ValueError("'rpl_file' requested but not present in fragment data.")

    @property
    def fragment(self) -> DatacubeFragment:
        """
        Property that returns the DatacubeFragment object.

        Returns:
            DatacubeFragment: The loaded fragment object.

        Raises:
            ValueError: If the fragment object has not been initialized.
        """
        if self._fragment is not None:
            return self._fragment
        else:
            raise ValueError("'fragment' requested but not present in fragment data.")

    @property
    def local_points(self) -> WarpSelection:
        """
        Property that returns the local warp selection points.

        Returns:
            WarpSelection: The local points.

        Raises:
            ValueError: If local points are not set.
        """
        if self._local_points is not None:
            return self._local_points
        else:
            raise ValueError(
                "'local_points' requested but not present in fragment data."
            )

    @property
    def target_points(self) -> WarpSelection:
        """
        Property that returns the target warp selection points.

        Returns:
            WarpSelection: The target points.

        Raises:
            ValueError: If target points are not set.
        """
        if self._target_points is not None:
            return self._target_points
        else:
            raise ValueError(
                "'target_points' requested but not present in fragment data."
            )

    @property
    def points(self) -> tuple[WarpSelection, WarpSelection]:
        """
        Property that returns a tuple of local and target points.

        Returns:
            tuple[WarpSelection, WarpSelection]: The local and target points.

        Raises:
            ValueError: If points tuple is not set.
        """
        if self._points is not None:
            return self._points
        else:
            raise ValueError("'points' requested but not present in fragment data.")

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
        _preview (bool): Indicates whether the stitching should be a preview or not (stitching on greyscale images vs. real data)
        _scaling (int): User supplied factor applied to the optimal scalar for scaling the contextual image that is being mapped to.
        _contextual_image_name (str): Name of the contextual image.
        _contextual_image_dimensions (Dimensions): Dimensions of the contextual image.
        _points (list[tuple[WarpSelection, WarpSelection]]): List containing local and target points for all fragments.
        _intensity_scales (list[float]): List containing all the intensitiy scales per fragment.
        fragment_data (list[FragmentData]): Metadata for the individual datacube fragments.
    """
    data_source: str
    cube_type: str
    fragment_data: list[FragmentData]

    _preview: bool | None
    _scaling: float | None
    _contextual_image_name: str | None
    _contextual_image_dimensions: Dimensions | None
    _points: list[tuple[WarpSelection, WarpSelection]] | None
    _intensity_scales: list[float] | None

    # Init
    def __init__(self, data: Dict[str, Any], data_source: str, is_stitching: bool = False):
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
        self.data_source = data_source

        # Verify data
        if data is None:
            raise ValueError("Invalid or missing JSON")

        # Cube type
        if data.get("type") not in ("elemental", "spectral"):
            raise ValueError("type must be 'elemental' or 'spectral'")

        self.cube_type = data["type"]

        # Preview
        if not isinstance(data.get("preview"), bool | None):
            raise ValueError("preview must be boolean")

        self._preview = data.get("preview")

        # Contextual image related variables
        if not isinstance(data.get("contextual_image"), str | None):
            raise ValueError("contextual_image must be string")

        self._contextual_image_name = data.get("contextual_image")
        self.init_contextual_image_dimensions()

        # Down scaling factor
        down_scaling = data.get("down_scaling")
        if not (isinstance(down_scaling, (int, float)) and 0 < down_scaling) and down_scaling is not None:
            raise ValueError("down_scaling must be a number larger than 0")

        self._scaling = down_scaling

        if is_stitching:
            # Intensity scales
            intensity_scales = data.get("intensity_scales")
            if not intensity_scales or not isinstance(intensity_scales, list):
                raise ValueError("intensity_scales must be a non-empty float list")

            intensity_scales_arr: list[float] = []
            for x in intensity_scales:
                if isinstance(x, bool):
                    raise ValueError("intensity_scales must contain only numbers")
                if isinstance(x, (int, float)):
                    intensity_scales_arr.append(float(x))
                else:
                    raise ValueError("intensity_scales must contain only numbers")

            self._intensity_scales = intensity_scales_arr
        
        # Fragments
        fragments = data.get("fragments")
        if not fragments or not isinstance(fragments, list):
            raise ValueError("fragments must be a non-empty list")

        self.fragment_data = []

        for i, frag in enumerate(fragments):
            if not isinstance(frag, dict):
                raise ValueError(f"fragments[{i}] must be an object")

            self.fragment_data.append(FragmentData(frag, self.data_source, self.cube_type, self._contextual_image_dimensions))

        # Gather point tuples from all fragments
        self._points = []
        for fragment in self.fragment_data:
            self._points.append(fragment.points)

    @property
    def contextual_image_dimensions(self) -> Dimensions:
        """
        Property that returns the dimensions of a contextual image if available.

        Returns:
            Dimensions: An object representing the dimensions of the contextual image.

        Raises:
            ValueError: If contextual_image_dimensions is not present.
        """
        if self._contextual_image_dimensions is not None:
            return self._contextual_image_dimensions
        else:
            raise ValueError("contextual_image_dimensions requested but contextual image not present in request parameters.")

    @property
    def points(self) -> list[tuple[WarpSelection, WarpSelection]]:
        """
        Property that returns the warp points for all fragments if available.

        Returns:
            list[tuple[WarpSelection, WarpSelection]]: A list containing tuples of warp points,
            representing the local and target warp points.

        Raises:
            ValueError: If points are not present in the data.
        """
        if self._points is not None:
            return self._points
        else:
            raise ValueError("'points' requested but no points present in request parameters.")

    @property
    def scaling(self) -> float:
        """
        Property that returns the scaling factor if available.

        Returns:
            float: Scaling factor.

        Raises:
            ValueError: If scaling is not present in the data.
        """
        if self._scaling is not None:
            return self._scaling
        else:
            raise ValueError("'scaling' requested but down_scale not in request parameters.")

    @property
    def preview(self) -> bool:
        """
        Property that returns whether current data is for a preview or not.

        Returns:
            bool: True if current data is for a preview, False otherwise.

        Raises:
            ValueError: If preview is not present in the data.
        """
        if self._preview is not None:
            return self._preview
        else:
            raise ValueError("'preview' requested but not in request parameters.")

    def init_contextual_image_dimensions(self):
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
        if not self._contextual_image_name:
            self._contextual_image_dimensions = None
            return

        # Contextual image dimensions
        image_path = _build_path(self._contextual_image_name, self.data_source)

        image = cv.imread(image_path, cv.IMREAD_GRAYSCALE)
        if image is None:
            raise FileNotFoundError(f"Failed to load contextual image: {image_path}")

        height, width = image.shape

        if width == 0 or height == 0:
            raise ValueError("Contextual image has invalid dimensions.")

        self._contextual_image_dimensions =  Dimensions(width, height)

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
            self._intensity_scales,
            self.points,
            self.contextual_image_dimensions,
            scalar,
            output_dir,
            self.data_source
        )

def _build_path(path_value: str, data_source: str) -> str:
    """
    Generates a path to the file in the provided data source from the project root directory.

    Args:
        path_value: The user-supplied relative path.
        data_source: Name of the data source.

    Returns:
        Path to the data source from the project root.
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

def get_greyscale_path(greyscale_name: str, data_source) -> str:
    """
    Generates and returns the file path for the greyscale image associated
    with the given datacube. The method ensures that the required directory
    structure exists before generating the path.

    Returns:
        str: The path to the greyscale image file.
    """
    generated_dir = _build_path(join("generated", "stitching"), data_source)
    os.makedirs(generated_dir, exist_ok=True)

    export_path = join(generated_dir, f"{greyscale_name}.png")
    return export_path

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
            (data.get_fragments()[0].channels + 1) # Spectral channels + 1 elemental channel
            * data.contextual_image_dimensions.width
            * data.contextual_image_dimensions.height
    )

    losses = optimizer.calculate_loss_percentage(optimal_scalar)

    return {"optimal_scalar": optimal_scalar, "full_size": reference_file_size, "losses": losses}

def create_recipe_file(recipe_file: str, datacube_dimensions: Dimensions, contextual_image_dimensions: Dimensions) -> str:
    from_height = datacube_dimensions.height
    from_width = datacube_dimensions.width
    to_height = contextual_image_dimensions.height
    to_width = contextual_image_dimensions.width

    with open(recipe_file, "w", encoding="utf-8") as f:
        f.write("Butterfly Registrator\n")
        f.write("1.0\n")
        f.write("control points\n")
        f.write("Assumes moving image(s) resized and padded to match target image dimensions\n")
        f.write("target\n")
        f.write("not_found.tif\n")
        f.write("moving\n")
        f.write("not_found.tif\n")
        f.write("x|y|x|y\n")
        # Top-left
        f.write(f"0|0|0|0\n")
        # Top-right
        f.write(f"{from_width-1}|0|{to_width-1}|0\n")
        # Bottom-left
        f.write(f"0|{from_height-1}|0|{to_height-1}\n")
        # Bottom-right
        f.write(f"{from_width-1}|{from_height-1}|{to_width-1}|{to_height-1}\n")
    return recipe_file

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
        export_path = get_greyscale_path(frag_data.datacube_filename, frag_data.data_source)

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
    all_conversions_successful = True

    for fragment_data in data.fragment_data:
        greyscale_path = get_greyscale_path(
            fragment_data.datacube_filename, fragment_data.data_source
        )

        # Generate greyscale if it does not exist yet
        if not exists(greyscale_path):
            generate_partial_greyscale(fragment_data)

    return all_conversions_successful

def load_greyscale_from_file(name: str, data_source: str):
    """
    Loads a greyscale image from a file specified by its name and data source. The function
    constructs the full file path using the provided name and data source, then reads the
    image in greyscale mode using OpenCV.

    Args:
        name (str): Name of the image file.
        data_source (str): Source or directory where the image file is located.

    Returns:
        Image: The loaded greyscale image.

    Raises:
        FileNotFoundError: If the image file cannot be found or loaded.
    """
    path = get_greyscale_path(name, data_source)
    greyscale_fragment = cv.imread(path, flags=cv.IMREAD_GRAYSCALE)
    if greyscale_fragment is None:
        raise FileNotFoundError(f"Failed to load greyscale image: {path}")
    return greyscale_fragment

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

    for fragment_data in data.fragment_data:
        greyscale_path = get_greyscale_path(fragment_data.datacube_filename, fragment_data.data_source)

        # Generate greyscale if it does not exist yet
        if not exists(greyscale_path):
            generate_partial_greyscale(fragment_data)

        greyscale_image = cv.imread(greyscale_path, flags=cv.IMREAD_GRAYSCALE)
        greyscales.append(greyscale_image)

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

    result_width, result_height = result_image.shape[:2]

    recipe_file_name = "preview_recipe.csv"
    create_recipe_file(
        _build_path(recipe_file_name, data.data_source),
        Dimensions(result_width, result_height),
        data.contextual_image_dimensions)

    # Prepare output directory
    output_dir = _build_path(join("generated", "stitching"), data.data_source)
    os.makedirs(output_dir, exist_ok=True)

    preview_file_name = "preview.png"

    # Save preview image
    preview_path = join(output_dir, preview_file_name)
    cv.imwrite(preview_path, result_image.astype(np.uint8))

    return {
        "status": "success",
        "preview": True,
        "preview_path": preview_file_name,
        "recipe_file": recipe_file_name,
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

    recipe_file_name = "stitched_recipe.csv"
    create_recipe_file(
        _build_path(recipe_file_name, data.data_source),
        Dimensions(result_fragment.width, result_fragment.height),
        data.contextual_image_dimensions)

    # Create a projection for verification
    projection = result_fragment.create_greyscale_projection()
    projection = normalize_image(projection)

    # Save projection image
    output_dir = _build_path(join("generated", "stitching"), data.data_source)
    os.makedirs(output_dir, exist_ok=True)

    projection_path = join(output_dir, "stitched_projection.png")
    cv.imwrite(projection_path, projection.astype(np.uint8))

    output_file_name = os.path.basename(result_fragment.datacube_file)

    workspace = get_workspace_dict(data.data_source)
    if(data.cube_type == "spectral"):
        workspace["spectralCubes"] = [{
            "name": "stitched_spectral_datacube",
            "rawLocation": output_file_name,
            "rplLocation": rpl_file if rpl_file else "",
            "recipeLocation": recipe_file_name
        }]
    else: 
        workspace["elementalCubes"] = [{
            "name": "stitched_elemental_datacube",
            "dataLocation": output_file_name,
            "recipeLocation": recipe_file_name
        }]
    update_workspace(data.data_source, workspace)

    return {
        "status": "success",
        "preview": False,
        "output_file": output_file_name,
        "type": "spectral" if result_fragment.is_spectral else "elemental",
        "rpl_file": rpl_file,
        "recipe_file": recipe_file_name,
        "dimensions": {
            "width": result_fragment.width,
            "height": result_fragment.height,
            "channels": result_fragment.channels,
        },
    }

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
        if not getattr(fragment, "is_spectral", False):
            LOG.info(f"Skipping non-spectral fragment: {cube_file}")
            cubes_skipped.append({
                "cube_file": cube_file,
                "reason": "not a spectral datacube"
            })
            continue
        
        # Check if already transposed (the file exists)
        if fragment.is_transposed:
            LOG.info(f"Fragment already transposed: {cube_file}")
            cubes_skipped.append({
                "cube_file": cube_file,
                "reason": "already transposed"
            })
            continue
        
        # Create a worker function for this specific fragment
        def create_worker(frag, ds, cf):
            """Closure to capture fragment, data_source, cube_file"""
            def transpose_worker():
                _transpose_cube_worker(frag, ds, cf, state_manager)
            return transpose_worker
        
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