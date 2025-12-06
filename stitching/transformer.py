from __future__ import annotations
from abc import ABC, abstractmethod
import numpy as np
import cv2 as cv
import matplotlib.pyplot as plt
from typing import Sequence, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from scipy.optimize import minimize_scalar
import os


def split_range(start: int, end: int, parts: int) -> list[tuple[int, int]]:
    """
    Helper utility to divide a range of integers into equal (or near-equal) chunks.
    Used to distribute the workload of processing channels across multiple threads.

    Args:
        start: Starting integer.
        end: Ending integer (exclusive).
        parts: Number of chunks to create.

    Returns:
        List of tuples, where each tuple is a (start, end) range.
    """
    if parts <= 0:
        raise ValueError("parts must be >= 1")
    if parts == 1:
        return [(start, end)]
    length = end - start
    base = length // parts
    remainder = length % parts

    result = []
    current = start

    for i in range(parts):
        # Distribute the remainder 1 by 1 across the first few chunks
        chunk_size = base + (1 if i < remainder else 0)
        next_pos = current + chunk_size
        result.append((current, next_pos))
        current = next_pos

    return result


def transpose_spectral_datacube(
    input_path: str,
    output_path: str,
    input_shape: tuple[int, int, int],
    output_shape: tuple[int, int, int],
    dtype: str,
    chunk_size: int = 100,
) -> None:
    """
    Transposes a spectral datacube file using memory mapping to maintain low RAM usage.
    Supports both (H, W, C) -> (C, H, W) and (C, H, W) -> (H, W, C).

    Args:
        input_path: Path to input file
        output_path: Path to output file
        input_shape: Shape of input data
        output_shape: Shape of output data
        dtype: NumPy dtype string
        chunk_size: Number of rows/channels to process at once
    """
    input_mmap = np.memmap(input_path, dtype=dtype, mode="r", shape=input_shape)
    output_mmap = np.memmap(output_path, dtype=dtype, mode="w+", shape=output_shape)

    print(f"Transposing: {input_shape} -> {output_shape}")
    print(f"File size: {input_mmap.nbytes / 1e9:.2f} GB")

    dim0, dim1, dim2 = input_shape

    # Case 1: (H, W, C) -> (C, H, W) - Chunk along height
    if input_shape[2] == output_shape[0]:
        for i in range(0, dim0, chunk_size):
            end_i = min(i + chunk_size, dim0)
            print(f"Processing rows {i} to {end_i} of {dim0}")

            # Read chunk: (chunk_h, W, C)
            chunk_data = input_mmap[i:end_i, :, :]

            # Transpose to: (C, chunk_h, W)
            chunk_transposed = chunk_data.transpose(2, 0, 1)

            # Write: all channels, specific height slice, all width
            output_mmap[:, i:end_i, :] = chunk_transposed

            if i % (chunk_size * 5) == 0:
                output_mmap.flush()

    # Case 2: (C, H, W) -> (H, W, C) - Chunk along channels
    elif input_shape[0] == output_shape[2]:
        for i in range(0, dim0, chunk_size):
            end_i = min(i + chunk_size, dim0)
            print(f"Processing channels {i} to {end_i} of {dim0}")

            # Read chunk: (chunk_c, H, W)
            chunk_data = input_mmap[i:end_i, :, :]

            # Transpose to: (H, W, chunk_c)
            chunk_transposed = chunk_data.transpose(1, 2, 0)

            # Write: all height, all width, specific channel slice
            output_mmap[:, :, i:end_i] = chunk_transposed

            if i % (chunk_size * 5) == 0:
                output_mmap.flush()
    else:
        raise ValueError(f"Unsupported transpose from {input_shape} to {output_shape}")

    output_mmap.flush()
    print("Transpose complete.\n")


class ScalarOptimizer:
    """
    Optimizes the scaling factor between two images based on user-selected
    corresponding regions (WarpSelections).

    This determines the relative "zoom" level difference between two datacube fragments
    to ensure they stitch together at the correct size.
    """

    def __init__(self, points: list[tuple[WarpSelection, WarpSelection]]):
        # List of paired regions: (Source Region, Destination/Reference Region)
        self.points = points

    def calculate_loss_percentage(self, scalar: float) -> list[int]:
        """Calculates the scaling error percentage for debugging/UI purposes."""
        return [
            round(self.get_scale_factor(src, dst, scalar) * 100, 1)
            for (src, dst) in self.points
        ]

    def find_best_scalar(self) -> tuple[float, float]:
        """
        Uses scalar minimization to find the optimal scaling factor.
        We want the scale factor where the calculated homography implies a
        relative scale of 1.0 (meaning the warped source matches the dest size).
        """
        # Bounded search between 0.1x and 2.0x zoom
        res = minimize_scalar(self.cost_function, bounds=(0.1, 2.0), method="bounded")
        return res.x, res.fun

    def get_scale_factor(
        self, src: WarpSelection, dst: WarpSelection, scalar: float
    ) -> float:
        """
        Calculates the Homography matrix (perspective transform) between source
        and destination points, then extracts the scaling component.
        """
        # Calculate Homography (H) using RANSAC to ignore outliers
        H, _ = cv.findHomography(src.get_points(), dst.get_points(scalar), cv.RANSAC)

        # Extract scaling from the Homography matrix.
        # H[0:2, 0] represents the transformation of the X-basis vector.
        # H[0:2, 1] represents the transformation of the Y-basis vector.
        # The norm of these gives the scaling factor in X and Y directions.
        s1 = np.linalg.norm(H[0:2, 0])
        s2 = np.linalg.norm(H[0:2, 1])

        # Geometric mean of X-scale and Y-scale
        scale = np.sqrt(s1 * s2)
        return scale

    def cost_function(self, scalar: float) -> float:
        """
        The objective function for the optimizer.
        We want the derived scale factor between the warped source and destination
        to be exactly 1.0. Any deviation is 'cost'.
        """
        total_cost = 0
        for src, dst in self.points:
            scale = self.get_scale_factor(src, dst, scalar)
            total_cost += (scale - 1) ** 2  # Least squares error
        return total_cost / len(self.points)


class DatacubeStitcher:
    """
    Main controller for stitching multiple DatacubeFragments into a single large datacube.
    Handles memory mapping, multithreading, perspective warping, and intensity normalization.
    """

    def __init__(
        self,
        fragments: Sequence[DatacubeFragment],
        intensity_scales: list[float],
        points: list[tuple[WarpSelection, WarpSelection]],
        frame: Dimensions,
        scalar: float = 1.0,
    ):
        self.fragments = fragments
        self.frame = frame  # Output canvas dimensions
        self.points = points  # Alignment points for creating perspective matrices
        self.intensity_scales = intensity_scales  # Brightness normalization factors
        self.scalar = scalar  # Global scaling factor

        # Calculate final canvas size
        self.scaled_height = int(frame.height * self.scalar)
        self.scaled_width = int(frame.width * self.scalar)

        # Validations
        if fragments is None or len(fragments) == 0:
            raise ValueError("No fragments provided")
        elif len(fragments) > 32:
            raise ValueError("Too many fragments provided, maximum is 32")
        elif len(intensity_scales) != len(fragments) or len(points) != len(fragments):
            raise ValueError(
                "Number of intensity scales, fragments, and point sets must match."
            )
        else:
            self.base_cube = fragments[0]
            # Ensure all fragments have compatible data types/channels before starting
            for cube in fragments[1:]:
                if not self.base_cube.are_compatible(cube):
                    raise ValueError("Incompatible datacubes")

        # Calculate the transformation matrices
        self.perspective_matrices = self.get_perspective_matrices()

        # Track transposed files for cleanup
        self.transposed_files: list[str] = []

    def stitch_greyscales(self, images: list[np.ndarray]):
        """
        Stitches standard 2D images (previews/projections) to verify alignment
        visually before committing to the heavy datacube stitch.
        """
        if len(images) != len(self.points):
            raise ValueError("Number of images must match number of point sets.")
        canvas = np.full((self.scaled_height, self.scaled_width), 0, dtype=np.float32)

        for i, image in enumerate(images):
            img = image.astype(np.float32)
            # Apply geometric warp
            warped_image = cv.warpPerspective(
                img,
                self.perspective_matrices[i],
                (self.scaled_width, self.scaled_height),
                flags=cv.INTER_NEAREST,  # Nearest neighbor to preserve raw data values
                borderValue=-1,
            )
            # Overlay non-border pixels
            mask = warped_image != -1
            canvas[mask] = warped_image[mask] * self.intensity_scales[i]

        display_img = canvas.copy()
        display_img[display_img == -1] = 0
        return display_img

    def rotate_cv(self, img, rotation):
        """Standardizes rotation handling using OpenCV constants."""
        if rotation == 0:
            return img
        elif rotation == 90:
            return cv.rotate(img, cv.ROTATE_90_COUNTERCLOCKWISE)
        elif rotation == 180:
            return cv.rotate(img, cv.ROTATE_180)
        elif rotation == 270:
            return cv.rotate(img, cv.ROTATE_90_CLOCKWISE)
        else:
            raise ValueError("Rotation must be 0, 90, 180, or 270")

    def _precalculate_masks(self) -> list[np.ndarray]:
        """
        Pre-calculates the boolean masks for each fragment.
        This prevents recalculating geometry for every single channel.
        """
        print("Pre-calculating geometry masks...")
        masks = []
        for i, frag in enumerate(self.fragments):
            # Create a dummy image with the dimensions of the fragment and rotate accordingly
            src_mask = np.full((frag.height, frag.width), 255, dtype=np.uint8)
            src_mask = self.rotate_cv(src_mask, frag.rotation)

            # Warp the square mask into the perspective shape
            warped_mask = cv.warpPerspective(
                src_mask,
                self.perspective_matrices[i],
                (self.scaled_width, self.scaled_height),
                flags=cv.INTER_NEAREST,
                borderValue=0,
            )
            masks.append(warped_mask > 0)
        return masks

    def fill_subset_layers(
        self,
        input_maps: list[np.memmap],
        output_map: np.memmap,
        masks: list[np.ndarray],
        channel_start: int,
        channel_end: int,
    ):
        """
        Worker function intended for threading.
        Stitches a specific range of channels (spectral slices) or elements.

        Args:
            input_maps: Open memory maps of the source files.
            output_map: Open memory map of the destination file.
            masks: Pre-calculated boolean masks for placement.
            channel_start/end: The range of channels this thread is responsible for.
        """
        # Pre-allocate reuseable buffers for this thread to prevent memory churn
        warp_buffers = [
            np.empty((self.scaled_height, self.scaled_width), dtype=np.float32)
            for _ in input_maps
        ]

        # Determine data layout
        is_spectral = self.base_cube.is_spectral()

        for channel in range(channel_start, channel_end):
            # Create the accumulator layer for this specific channel
            layer = np.zeros((self.scaled_height, self.scaled_width), dtype=np.float32)

            for i, input_map in enumerate(input_maps):
                # Both spectral and elemental now use (C, H, W) format
                layer_fragment = input_map[channel, :, :].astype(np.float32, copy=False)

                # Apply intensity normalization (if brightness differs between scans)
                scale = self.intensity_scales[i]
                if scale != 1.0:
                    layer_fragment = np.multiply(
                        layer_fragment, scale, dtype=np.float32
                    )

                # Rotate data if the scan was rotated relative to the others
                layer_fragment = self.rotate_cv(
                    layer_fragment, self.fragments[i].rotation
                )

                # Warp the data into position using OpenCV
                cv.warpPerspective(
                    layer_fragment,
                    self.perspective_matrices[i],
                    (self.scaled_width, self.scaled_height),
                    flags=cv.INTER_NEAREST,  # No interpolation to preserve data integrity
                    borderValue=0,
                    dst=warp_buffers[i],  # Write directly to pre-allocated buffer
                )

                # Compose using pre-calculated mask
                # Accessing the specific mask for this fragment
                mask = masks[i]
                # Write warped data onto the layer only where the mask is valid
                layer[mask] = warp_buffers[i][mask]

            # Write the completed stitched layer to the output memory map
            # Output is always in (C, H, W) format during stitching
            output_map[channel, :, :] = (
                np.clip(layer, 0, 255).astype(output_map.dtype)
                if is_spectral
                else layer
            )

    def fill_layers(self, output_map: np.memmap) -> None:
        """
        Orchestrator for the stitching process.
        Sets up memory maps, calculates masks, and dispatches threads.
        """
        # Load source files as memory maps (lazy loading)
        maps = [cube.load_datacube() for cube in self.fragments]

        # Calculate geometric masks once
        masks = self._precalculate_masks()

        # Determine thread count.
        workers = os.cpu_count() if self.base_cube.is_spectral() else 1

        print(f"Starting stitching with {workers} workers...")

        with ThreadPoolExecutor(max_workers=workers) as executor:
            # Create work items (futures) based on channel ranges
            futures = [
                executor.submit(
                    self.fill_subset_layers, maps, output_map, masks, start, end
                )
                for (start, end) in split_range(0, self.base_cube.channels, workers)
            ]

            # Track progress
            completed = 0
            for _ in as_completed(futures):
                completed += 1
                print(f"Worker chunk {completed}/{len(futures)} finished.")

    def stitch_datacubes(self) -> DatacubeFragment:
        """
        Entry point for stitching. Creates the output file and starts filling it.
        Returns the new DatacubeFragment representing the stitched result.
        """
        if len(self.fragments) != len(self.points):
            raise ValueError("Number of images must match number of point sets.")

        if self.base_cube.is_spectral():
            # Handle Spectral Data (Format: .raw + .rpl)
            # Transpose all input files to (C, H, W)
            print("\n=== Transposing input files to (C, H, W) format ===")
            transposed_fragments = []
            for frag in self.fragments:
                transposed_frag = frag.create_transposed_version()
                transposed_fragments.append(transposed_frag)
                self.transposed_files.append(transposed_frag.datacube_file)

            # Replace fragments with transposed versions
            original_fragments = self.fragments
            self.fragments = transposed_fragments

            # Perform stitching in (C, H, W) format
            datacube_file_temp = "stitched_spectral_temp.raw"
            datacube_file = "stitched_spectral.raw"
            rpl_file = "stitched_spectral.rpl"

            print(
                "\n=== Stitching in (C, H, W) format ===\nEstimated file size is:",
                (self.scaled_width * self.scaled_height * self.base_cube.channels)
                / (1024**3),
                "GB",
                f"with dimensions: {self.base_cube.channels} * {self.scaled_height} * {self.scaled_width}",
            )

            # Create temporary output in (C, H, W) format
            output_map = np.memmap(
                datacube_file_temp,
                dtype=self.base_cube.data_type,
                offset=0,
                mode="w+",
                shape=(self.base_cube.channels, self.scaled_height, self.scaled_width),
            )
            self.fill_layers(output_map)
            output_map.flush()
            del output_map

            # Transpose output back to (H, W, C)
            print("\n=== Transposing output back to (H, W, C) format ===")
            transpose_spectral_datacube(
                datacube_file_temp,
                datacube_file,
                (self.base_cube.channels, self.scaled_height, self.scaled_width),
                (self.scaled_height, self.scaled_width, self.base_cube.channels),
                self.base_cube.data_type,
            )

            # Write RPL file
            SpectralDatacubeFragment.write_rpl_file(
                rpl_file,
                self.base_cube.rpl_meta,
                self.scaled_width,
                self.scaled_height,
            )

            # Cleanup temporary files
            print("\n=== Cleaning up temporary files ===")
            for temp_file in self.transposed_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"Removed: {temp_file}")
            if os.path.exists(datacube_file_temp):
                os.remove(datacube_file_temp)
                print(f"Removed: {datacube_file_temp}")

            # Restore original fragments
            self.fragments = original_fragments

            return SpectralDatacubeFragment.from_file(datacube_file, rpl_file)
        else:
            # Handle Elemental Data (Format: .dms)
            datacube_file = "stitched_elemental.dms"
            return ElementalDatacubeFragment.write_file(
                datacube_file,
                self.scaled_width,
                self.scaled_height,
                self.base_cube.channels,
                self.base_cube.elements,
                lambda output_map: self.fill_layers(output_map),
            )

    def get_perspective_matrices(self) -> list[np.ndarray]:
        """Calculates CV2 Perspective Transform Matrix for each fragment."""
        perspective_matrices = []
        for i, (src, dst) in enumerate(self.points):
            # Calculate transform from source points to scaled destination points
            perspective_matrice = cv.getPerspectiveTransform(
                src.get_points(), dst.get_points(self.scalar)
            )
            perspective_matrices.append(perspective_matrice)
        return perspective_matrices


class WarpSelection:
    """
    Represents a quadrilateral selection in an image used for alignment.
    Defines 4 points corresponding to a physical feature.
    """

    def __init__(
        self,
        top_left: tuple[int, int],
        top_right: tuple[int, int],
        bottom_left: tuple[int, int],
        bottom_right: tuple[int, int],
    ):
        self.top_left = top_left
        self.top_right = top_right
        self.bottom_left = bottom_left
        self.bottom_right = bottom_right

    def get_points(self, scalar: float = 1.0) -> np.ndarray:
        """
        Returns the 4 points as a float32 array, optionally scaled.
        Scaling is used when mapping to the destination frame, which might be rescaled.
        """
        if scalar != 1.0:
            return np.array(
                [
                    (int(self.top_left[0] * scalar), int(self.top_left[1] * scalar)),
                    (int(self.top_right[0] * scalar), int(self.top_right[1] * scalar)),
                    (
                        int(self.bottom_left[0] * scalar),
                        int(self.bottom_left[1] * scalar),
                    ),
                    (
                        int(self.bottom_right[0] * scalar),
                        int(self.bottom_right[1] * scalar),
                    ),
                ],
                dtype=np.float32,
            )
        else:
            return np.array(
                [self.top_left, self.top_right, self.bottom_left, self.bottom_right],
                dtype=np.float32,
            )


class Dimensions:
    """Simple struct to hold width and height."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height


class DatacubeFragment(ABC):
    """
    Abstract Base Class for different types of data fragments.
    Handles common properties like dimensions and rotation.
    """

    def __init__(
        self, datacube_file: str, width: int, height: int, channels: int, rotation: int
    ):
        self.datacube_file = datacube_file
        self.width = width
        self.height = height
        self.channels = channels
        if (rotation % 90) != 0:
            raise ValueError("Rotation must be a multiple of 90 degrees")
        self.rotation = rotation % 360

    @abstractmethod
    def are_compatible(self, datacube) -> bool:
        """Checks if another datacube has matching metadata (channels, types)."""
        pass

    @abstractmethod
    def load_datacube(self) -> np.memmap:
        """Opens the file as a numpy memory map."""
        pass

    @abstractmethod
    def is_spectral(self) -> bool:
        """Returns True if the data is Spectral, False if Elemental."""
        pass

    def export_projection(self, file: str) -> None:
        """Saves a summed/averaged 2D projection of the datacube as a JPG."""
        picture = self.create_greyscale_projection()
        plt.imsave(
            file,
            picture,
            cmap="gray",
            format="jpg",
            vmin=picture.min(),
            vmax=picture.max(),
        )

    def create_greyscale_projection(self, chunk_size: int = 256) -> np.ndarray:
        """
        Collapses the multidimensional cube into a 2D image.
        Used for visualization/alignment references.
        """
        memmap = self.load_datacube()
        out = np.zeros((self.height, self.width), dtype=np.float32)

        if self.is_spectral():
            # Spectral data is now in (C, H, W) format after transpose
            # Iterate over channels and average them
            acc = np.zeros((self.height, self.width), dtype=np.float32)
            for c0 in range(0, self.channels, chunk_size):
                c1 = min(c0 + chunk_size, self.channels)
                print("Reducing chunk channels", c0, "to", c1, "of", self.channels)
                chunk_data = memmap[c0:c1, :, :]
                acc += chunk_data.sum(axis=0)
                memmap.flush()
            out[:, :] = (acc / self.channels).astype(np.float32)
        else:
            # Elemental: Iterate over channels (C-axis) and sum them up
            acc = np.zeros((self.height, self.width), dtype=np.float32)
            for c0 in range(0, self.channels, chunk_size):
                c1 = min(c0 + chunk_size, self.channels)
                print("Reducing chunk channels", c0, "to", c1, "of", self.channels)
                chunk_data = memmap[c0:c1, :, :]
                acc += chunk_data.sum(axis=0)
            out[:, :] = (acc / self.channels).astype(np.float32)
        return out


class ElementalDatacubeFragment(DatacubeFragment):
    """
    Handles Elemental datacubes.
    Layout: (Channels, Height, Width) - Planar layout.
    File format: ASCII Header -> Binary Data -> ASCII Footer.
    """

    def __init__(
        self,
        datacube_file: str,
        width: int,
        height: int,
        channels: int,
        offset: int,
        rotation: int,
        elements: list[str],
    ):
        super().__init__(datacube_file, width, height, channels, rotation)
        self.offset = offset  # Byte offset where binary data begins
        self.elements = elements  # List of element names (e.g., "Fe", "Cu")

    @classmethod
    def from_file(cls, datacube_file: str, rotation: int = 0):
        """Parses the custom header to extract dimensions and offsets."""
        with open(datacube_file, "rb") as file:
            file.readline()  # Skip first line
            dimensions_list = file.readline().decode("ascii").strip().split()
            width, height, channels = [int(dim) for dim in dimensions_list]
            header_size = file.tell()

            # Jump past the binary data to read the footer (element names)
            # 4 bytes per float * W * H * C
            file.seek(width * height * channels * 4, 1)
            elements = []
            for _ in range(channels):
                elements.append(file.readline().decode("ascii").strip())
        return cls(
            datacube_file, width, height, channels, header_size, rotation, elements
        )

    def load_datacube(self) -> np.memmap:
        """Loads data with shape (C, H, W)."""
        print("Loading elemental datacube:", self.datacube_file)
        memmap = np.memmap(
            self.datacube_file,
            dtype=np.float32,
            mode="r",
            offset=self.offset,
            shape=(self.channels, self.height, self.width),
        )
        return memmap

    def are_compatible(self, datacube) -> bool:
        if not isinstance(datacube, ElementalDatacubeFragment):
            return False
        # Must have same elements in same order to be stitchable
        return self.channels == datacube.channels and np.array_equal(
            self.elements, datacube.elements
        )

    @staticmethod
    def write_file(
        datacube_file: str,
        width: int,
        height: int,
        channels: int,
        elements: list[str],
        content_write_function: Callable[[np.ndarray]],
    ) -> ElementalDatacubeFragment:
        """Creates a new .dms file with header, fills it via callback, then appends footer."""
        header = ElementalDatacubeFragment.create_file_header(width, height, channels)

        # Write Header
        with open(datacube_file, "wb") as f:
            f.write(header)

        # Create Read/Write Memmap to fill binary data
        output_map = np.memmap(
            datacube_file,
            dtype=np.float32,
            offset=len(header),
            mode="r+",
            shape=(channels, height, width),
        )
        # Execute the filling logic (via DatacubeStitcher)
        content_write_function(output_map)
        output_map.flush()

        # Write Footer
        footer = ElementalDatacubeFragment.create_file_footer(elements)
        with open(datacube_file, "ab") as f:
            f.write(footer)

        return ElementalDatacubeFragment.from_file(datacube_file)

    @staticmethod
    def create_file_header(width: int, height: int, channels: int) -> bytes:
        header_lines = ["2\n", f"{width:10d}{height:10d}{channels:11d}\n"]
        return "".join(header_lines).encode("ascii")

    @staticmethod
    def create_file_footer(elements: list[str]) -> bytes:
        footer_text = "\r\n".join(elements) + "\r\n"
        return footer_text.encode("ascii")

    def is_spectral(self):
        return False


class SpectralDatacubeFragment(DatacubeFragment):
    """
    Handles Spectral datacubes.
    Original Layout: (Height, Width, Channels) - Pixel-vector layout.
    Transposed Layout: (Channels, Height, Width) - Channel-planar layout for efficient access.
    Format:
       1. .raw file: Pure binary data.
       2. .rpl file: ASCII Metadata.
    """

    def __init__(
        self,
        datacube_file: str,
        width: int,
        height: int,
        channels: int,
        offset: int,
        data_type,
        rotation: int,
        rpl_meta: dict,
        is_transposed: bool = False,
    ):
        super().__init__(datacube_file, width, height, channels, rotation)
        self.offset = offset
        self.data_type = data_type  # Numpy dtype string
        self.rpl_meta = rpl_meta  # Raw dictionary of the RPL file
        self.is_transposed = is_transposed  # Track if file is in (C, H, W) format

    @classmethod
    def from_file(cls, datacube_file: str, rpl_file: str, rotation: int = 0):
        """Parses the .rpl sidecar file to configure the reader."""
        meta = cls.parse_rpl_file(rpl_file)

        width = meta.get("width", 0)
        height = meta.get("height", 0)
        channels = meta.get("depth", 0)
        offset = meta.get("offset", 0)

        # Determine numpy dtype based on RPL strings
        data_len = meta.get("data-Length", 0)
        if data_len not in (1, 2, 4, 8):
            raise ValueError(f"Unsupported element size: {data_len} bytes")

        data_order = meta.get("byte-order")
        data_type = meta.get("data-type")
        dtype_signed = "u" if data_type == "unsigned" else "i"
        dtype_order = ">" if data_order == "big-endian" else "<"
        dtype = f"{dtype_order}{dtype_signed}{data_len}"  # e.g., '<u2'

        return cls(
            datacube_file, width, height, channels, offset, dtype, rotation, meta, False
        )

    @classmethod
    def parse_rpl_file(cls, rpl_file: str) -> dict:
        """Reads key-value pairs from Lispix .rpl files."""
        meta: dict[str, int | str] = {}
        with open(rpl_file) as file:
            for line in file:
                parts = line.strip().split()
                if len(parts) >= 2:
                    key, value = parts[0], parts[-1]
                    try:
                        value = int(value)
                    except ValueError:
                        pass
                    meta[key] = value
        return meta

    def is_spectral(self):
        return True

    def load_datacube(self):
        """Loads data with appropriate shape based on transpose state."""
        print("Loading spectral datacube:", self.datacube_file)
        if self.is_transposed:
            # Transposed format: (C, H, W)
            shape = (self.channels, self.height, self.width)
        else:
            # Original format: (H, W, C)
            shape = (self.height, self.width, self.channels)

        memmap: np.memmap = np.memmap(
            self.datacube_file,
            dtype=self.data_type,
            mode="r",
            offset=self.offset,
            shape=shape,
        )
        return memmap

    def create_transposed_version(self) -> SpectralDatacubeFragment:
        """
        Creates a transposed version of this datacube: (H, W, C) -> (C, H, W).
        Returns a new SpectralDatacubeFragment pointing to the transposed file.
        """
        if self.is_transposed:
            # Already transposed, return self
            return self

        # Generate transposed filename
        base_name = os.path.splitext(self.datacube_file)[0]
        transposed_file = f"{base_name}_transposed.raw"

        print(f"\nTransposing {self.datacube_file} -> {transposed_file}")

        # Perform transpose
        transpose_spectral_datacube(
            self.datacube_file,
            transposed_file,
            (self.height, self.width, self.channels),
            (self.channels, self.height, self.width),
            self.data_type,
        )

        # Create new fragment pointing to transposed file
        return SpectralDatacubeFragment(
            transposed_file,
            self.width,
            self.height,
            self.channels,
            0,  # No offset for transposed files
            self.data_type,
            self.rotation,
            self.rpl_meta,
            is_transposed=True,
        )

    def are_compatible(self, datacube) -> bool:
        if not isinstance(datacube, SpectralDatacubeFragment):
            return False
        return (
            self.channels == datacube.channels and self.data_type == datacube.data_type
        )

    @staticmethod
    def write_rpl_file(rpl_file: str, rpl_meta: dict, width: int, height: int) -> None:
        """Writes a metadata rpl file."""
        rpl_meta = rpl_meta.copy()
        rpl_meta["width"] = width
        rpl_meta["height"] = height
        rpl_meta["offset"] = 0
        with open(rpl_file, "w") as f:
            for key, value in rpl_meta.items():
                f.write(f"{key:<12}\t{value}\n")

    @staticmethod
    def write_file(
            datacube_file: str,
            rpl_file: str,
            rpl_meta: dict,
            data_type: str,
            width: int,
            height: int,
            channels: int,
            content_write_function: Callable[[np.memmap]],
    ) -> SpectralDatacubeFragment:
        """Creates .raw and .rpl files and fills them via callback."""
        output_map = np.memmap(
            datacube_file,
            dtype=data_type,
            offset=0,
            mode="w+",
            shape=(height, width, channels),
        )
        content_write_function(output_map)
        output_map.flush()
        SpectralDatacubeFragment.write_rpl_file(rpl_file, rpl_meta, width, height)
        return SpectralDatacubeFragment.from_file(datacube_file, rpl_file)