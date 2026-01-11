from __future__ import annotations

from enum import Enum

import cv2 as cv
import numpy as np
from scipy.optimize import minimize_scalar

class TransposeMode(Enum):
    HWC_TO_CHW = "hwc_to_chw"  # (H, W, C) -> (C, H, W)
    CHW_TO_HWC = "chw_to_hwc"  # (C, H, W) -> (H, W, C)

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
        total_height: int
    ):
        """
        Initializes a WarpSelection object with given corner coordinates.

        Args:
            top_left: A tuple of two integers representing the x and y coordinates
                of the top-left corner of the rectangle.
            top_right: A tuple of two integers representing the x and y coordinates
                of the top-right corner of the rectangle.
            bottom_left: A tuple of two integers representing the x and y coordinates
                of the bottom-left corner of the rectangle.
            bottom_right: A tuple of two integers representing the x and y coordinates
                of the bottom-right corner of the rectangle.
            total_height: The total height of the related image. Used for converting cartesian coordinated to graphic/screen coordinates.
        """
        self.top_left = (top_left[0], total_height - top_left[1])
        self.top_right = (top_right[0], total_height - top_right[1])
        self.bottom_left = (bottom_left[0], total_height - bottom_left[1])
        self.bottom_right = (bottom_right[0], total_height - bottom_right[1])

    def get_points(self, scalar: float = 1.0) -> np.ndarray:
        """
        Returns the 4 points as a float32 array, optionally scaled.
        Scaling is used when mapping to the destination frame, which might be rescaled.
        """
        if scalar != 1.0:
            return np.array(
                [
                    (
                        float(self.top_left[0] * scalar),
                        float(self.top_left[1] * scalar)),
                    (
                        float(self.top_right[0] * scalar),
                        float(self.top_right[1] * scalar)),
                    (
                        float(self.bottom_left[0] * scalar),
                        float(self.bottom_left[1] * scalar),
                    ),
                    (
                        float(self.bottom_right[0] * scalar),
                        float(self.bottom_right[1] * scalar),
                    ),
                ],
                dtype=np.float32,
            )
        else:
            return np.array(
                [self.top_left, self.top_right, self.bottom_left, self.bottom_right],
                dtype=np.float32,
            )

    def are_within(self, width, height) -> bool:
        """Checks if all points are within the given width and height."""
        for x, y in (
            self.top_left,
            self.top_right,
            self.bottom_left,
            self.bottom_right,
        ):
            if not (0 <= x < width and 0 <= y < height):
                return False
        return True

    def __str__(self) -> str:
        """
        Returns a string representation of the quadrilateral points
        based on the get_points method.
        """
        points = self.get_points()
        return (
            f"WarpSelection(\n"
            f"  TL: {points[0]}, TR: {points[1]},\n"
            f"  BL: {points[2]}, BR: {points[3]}\n"
            f")"
        )

class Dimensions:
    """Simple struct to hold width and height."""

    def __init__(self, width: int, height: int):
        """
        Simple struct to hold width and height.

        Args:
            width (int): The width.
            height (int): The height.
        """
        self.width = width
        self.height = height


class ScalarOptimizer:
    """
    Optimizes the scaling factor between two images based on user-selected
    corresponding regions (WarpSelections).

    This determines the relative "zoom" level difference between two datacube fragments
    to ensure they stitch together at the correct size.
    """

    def __init__(self, points: list[tuple[WarpSelection, WarpSelection]]):
        """
        Initialize the ScalarOptimizer with corresponding region pairs.

        Args:
            points: A list of tuples, each containing a pair of WarpSelection objects
                    (local, target) that represent corresponding regions between
                    two images to be aligned.
        """
        self.points = points

    def calculate_loss_percentage(self, scalar: float) -> list[float]:
        """Calculates the scaling error percentage for debugging/UI purposes."""
        return [
            round(self.get_scale_factor(src, dst, scalar) * 100, 8)
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
        total_cost = 0.0
        for src, dst in self.points:
            scale = self.get_scale_factor(src, dst, scalar)
            total_cost += (scale - 1) ** 2  # Least squares error
        return total_cost / len(self.points)


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
    mode: TransposeMode,
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

    dim0, dim1, dim2 = input_shape

    # Case 1: (H, W, C) -> (C, H, W) - Chunk along height
    if mode == TransposeMode.HWC_TO_CHW:
        for i in range(0, dim0, chunk_size):
            end_i = min(i + chunk_size, dim0)

            # Read chunk: (chunk_h, W, C)
            chunk_data = input_mmap[i:end_i, :, :]

            # Transpose to: (C, chunk_h, W)
            chunk_transposed = chunk_data.transpose(2, 0, 1)

            # Write: all channels, specific height slice, all width
            output_mmap[:, i:end_i, :] = chunk_transposed

            if i % (chunk_size * 5) == 0:
                output_mmap.flush()

    # Case 2: (C, H, W) -> (H, W, C) - Chunk along channels
    elif mode == TransposeMode.CHW_TO_HWC:
        for i in range(0, dim0, chunk_size):
            end_i = min(i + chunk_size, dim0)

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


def rotate_cv(img, rotation):
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

def normalize_image(data: np.ndarray) -> np.ndarray:
    """
    Normalizes data in the image to range 0-255

    Args:
        data: numpy array to be normalized

    Returns:
        Normalized numpy array

    """
    min, max = np.min(data), np.max(data)
    out = np.clip((data - min) / (max - min) * 255, 0, 255).astype(np.uint8)

    return out