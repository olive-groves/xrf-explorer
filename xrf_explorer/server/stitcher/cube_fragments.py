from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Callable

import numpy as np

from xrf_explorer.server.stitcher.helper import transpose_spectral_datacube, rotate_cv


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

    def create_recipe_file(self, recipe_file: str, datacube_dimensions: tuple[int, int], contextual_image_dimensions: tuple[int, int]) -> str:
        from_height, from_width = datacube_dimensions
        to_height, to_width = contextual_image_dimensions

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


    def create_greyscale_projection(self, chunk_size: int = 256) -> np.ndarray:
        """
        Collapses the multidimensional cube into a 2D image.
        Used for visualization/alignment references.
        """
        memmap = self.load_datacube()

        if self.is_spectral():
            data = np.mean(memmap, axis=2)
        else: # Elemental
            data = np.mean(memmap, axis=0)

        rotated = rotate_cv(data, self.rotation)

        return rotated


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
