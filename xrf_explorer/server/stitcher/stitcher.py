from __future__ import annotations
import numpy as np
import cv2 as cv
from typing import Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from os.path import join

from xrf_explorer.server.stitcher.cube_fragments import DatacubeFragment, ElementalDatacubeFragment, \
    SpectralDatacubeFragment
from xrf_explorer.server.stitcher.helper import WarpSelection, Dimensions, split_range, transpose_spectral_datacube, \
    rotate_cv


class DatacubeStitcher:
    """
    Main controller for stitching multiple DatacubeFragments into a single large datacube.
    Handles memory mapping, multithreading, perspective warping.
    """

    def __init__(
        self,
        fragments: Sequence[DatacubeFragment],
        points: list[tuple[WarpSelection, WarpSelection]],
        frame: Dimensions,
        scalar: float = 1.0,
        outputdir: str = None,
    ):
        self.fragments = fragments
        self.frame = frame  # Output canvas dimensions
        self.points = points  # Alignment points for creating perspective matrices
        self.scalar = scalar  # Global scaling factor
        self.outputdir = outputdir

        # Calculate final canvas size
        self.scaled_height = int(frame.height * self.scalar)
        self.scaled_width = int(frame.width * self.scalar)

        # Validations
        if fragments is None or len(fragments) == 0:
            raise ValueError("No fragments provided")
        elif len(fragments) > 32:
            raise ValueError("Too many fragments provided, maximum is 32")
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
            canvas[mask] = warped_image[mask]

        display_img = canvas.copy()
        display_img[display_img == -1] = 0
        return display_img

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
            src_mask = rotate_cv(src_mask, frag.rotation)

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

                # Rotate data if the scan was rotated relative to the others
                layer_fragment = rotate_cv(
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
            print(f"Number of points {len(self.points)} does not match number of fragments {len(self.fragments)}")
            raise ValueError("Number of images must match number of point sets.")

        if self.base_cube.is_spectral():
            # Handle Spectral Data (Format: .raw + .rpl)
            # Transpose all input files to (C, H, W)
            print("\n=== Transposing input files to (C, H, W) format ===")
            transposed_fragments = []
            for frag in self.fragments:
                transposed_frag: SpectralDatacubeFragment = frag.create_transposed_version()
                transposed_fragments.append(transposed_frag)
                self.transposed_files.append(transposed_frag.datacube_file)

            # Replace fragments with transposed versions
            original_fragments = self.fragments
            self.fragments = transposed_fragments

            # Perform stitching in (C, H, W) format
            datacube_file_temp = join(self.outputdir, "stitched_spectral_temp.raw")
            datacube_file = join(self.outputdir, "stitched_spectral.raw")
            rpl_file = join(self.outputdir, "stitched_spectral.rpl")

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
            print(f"dimensions: {self.base_cube.channels} * {self.scaled_height} * {self.scaled_width}",)
            # Handle Elemental Data (Format: .dms)
            datacube_file = join(self.outputdir, "stitched_elemental.dms")
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


