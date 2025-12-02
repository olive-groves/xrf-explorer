from __future__ import annotations
from abc import ABC, abstractmethod
import numpy as np
import cv2 as cv
import matplotlib.pyplot as plt
from typing import Sequence, Callable
from concurrent.futures import ThreadPoolExecutor, wait
import queue
import os
from scipy.optimize import minimize_scalar

def split_range(start, end, parts):
    if parts <= 0:
        raise ValueError("parts must be >= 1")
    if (parts == 1):
        return [(start, end)]
    length = end - start
    base = length // parts
    remainder = length % parts

    result = []
    current = start

    for i in range(parts):
        chunk_size = base + (1 if i < remainder else 0)
        next_pos = current + chunk_size
        result.append((current, next_pos))
        current = next_pos

    return result

class ScalarOptimizer:

    def __init__(self, points: list[tuple[WarpSelection, WarpSelection]]):
        self.points = points

    def calculate_loss_percentage(self, scalar: float) -> list[int]:
        return [round(self.get_scale_factor(src, dst, scalar) * 100, 1) for (src, dst) in self.points]

    def find_best_scalar(self) -> tuple[float, float]:
        res = minimize_scalar(self.cost_function, bounds=(0.1, 2.0), method='bounded')
        return res.x, res.fun

    def get_scale_factor(self, src: WarpSelection, dst: WarpSelection, scalar: float) -> float:
        H, _ = cv.findHomography(src.get_points(), dst.get_points(scalar), cv.RANSAC)
        s1 = np.linalg.norm(H[0:2, 0])
        s2 = np.linalg.norm(H[0:2, 1])
        scale = np.sqrt(s1 * s2)
        return scale

    def cost_function(self, scalar: float) -> float:
        total_cost = 0
        for (src, dst) in self.points:
            scale = self.get_scale_factor(src, dst, scalar)
            total_cost += (scale - 1)**2
        return total_cost/len(self.points)

class DatacubeStitcher():
    def __init__(self, fragments: Sequence[DatacubeFragment], intensity_scales: list[float], points: list[tuple[WarpSelection, WarpSelection]], frame: Dimensions, scalar: float = 1.0):
        self.fragments = fragments
        self.frame = frame
        self.points = points
        self.intensity_scales = intensity_scales
        self.scalar = scalar
        self.scaled_height = int(frame.height * self.scalar)
        self.scaled_width = int(frame.width * self.scalar)

        if (fragments is None or len(fragments) == 0):
            raise ValueError("No fragments provided")
        elif (len(fragments) > 32):
            raise ValueError("Too many fragments provided, maximum is 32")
        elif (len(intensity_scales) != len(fragments) or len(fragments) != len(fragments) or len(points) != len(fragments)):
            raise ValueError("Number of intensity scales, fragments, and point sets must match.")
        else:
            self.base_cube = fragments[0]
            for cube in fragments[1:]:
                if not self.base_cube.are_compatible(cube):
                    raise ValueError("Incompatible datacubes")
        self.perspective_matrices = self.get_perspective_matrices()        
    
    def stitch_greyscales(self, images: list[np.ndarray]):   
        if (len(images) != len(self.points)):
            raise ValueError("Number of images must match number of point sets.")
        canvas = np.full((self.scaled_height, self.scaled_width), 0, dtype=np.float32)
        for i, image in enumerate(images):
            img = image.astype(np.float32)
            warped_image = cv.warpPerspective(img, self.perspective_matrices[i], (self.scaled_width, self.scaled_height), flags=cv.INTER_NEAREST, borderValue=-1)
            mask = warped_image != -1
            canvas[mask] = warped_image[mask] * self.intensity_scales[i]
        
        display_img = canvas.copy()
        display_img[display_img == -1] = 0
        return display_img

    def rotate_cv(self, img, rotation):
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

    def write_buffered_channel(self, output: np.memmap, input: np.ndarray, channel: int, buffer_size: int = 128) -> None:
        height, _ = input.shape
        for y0 in range(0, height, buffer_size):
            y1 = min(y0 + buffer_size, height)
            output[y0:y1, :, channel] = input[y0:y1, :]

    def read_buffered_channel(self, input: np.memmap, channel: int, buffer_size: int = 128) -> np.ndarray:
        height, width, _ = input.shape
        out = np.empty((height, width), dtype=input.dtype)
        for y0 in range(0, height, buffer_size):
            y1 = min(y0 + buffer_size, height)
            out[y0:y1, :] = input[y0:y1, :, channel]
        return out


    def fill_subset_layers(self, update: queue.Queue, input_maps: list[np.memmap], output_map: np.memmap, channel_start: int, channel_end: int):
        warp_buffers = [ np.empty((self.scaled_height, self.scaled_width), dtype=np.float32) for _ in input_maps]
        cached_mask = [None] * len(self.fragments)
        
        for channel in range(channel_start, channel_end):
            layer = np.full((self.scaled_height, self.scaled_width), 0, dtype=np.float32)
            for i, input_map in enumerate(input_maps):

                if self.base_cube.is_spectral():
                    layer_fragment = self.read_buffered_channel(input_map, channel).astype(np.float32, copy=False)
                else: 
                    layer_fragment = input_map[channel, :, :]
                scale = self.intensity_scales[i]
                if (scale != 1.0):
                    layer_fragment = np.multiply(layer_fragment, scale, dtype=np.float32)
                layer_fragment = self.rotate_cv(layer_fragment, self.fragments[i].rotation)
                cv.warpPerspective(layer_fragment, self.perspective_matrices[i], (self.scaled_width, self.scaled_height), flags=cv.INTER_NEAREST, borderValue=-1, dst=warp_buffers[i])
                if cached_mask[i] is None:
                    cached_mask[i] = (warp_buffers[i] != -1)
                np.copyto(layer, warp_buffers[i], where=cached_mask[i])
            if self.base_cube.is_spectral():
                 #layer = np.clip(layer, 0, 255).astype(output_map.dtype)
                 self.write_buffered_channel(output_map, np.clip(layer, 0, 255).astype(output_map.dtype), channel)
                 #output_map[:, :, channel] = np.clip(layer, 0, 255).astype(output_map.dtype)
            else: 
                output_map[channel, :, :] = layer

            update.put(1)

    def fill_layers(self, output_map: np.memmap) -> None:
        maps = []
        updates = queue.Queue()
        maps = [cube.load_datacube() for cube in self.fragments]
        
        workers = os.cpu_count() if self.base_cube.is_spectral() else 1
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(self.fill_subset_layers, updates, maps, output_map, start, end)
                for (start, end) in split_range(0, self.base_cube.channels, workers)
            ]
            completed = 0
            while completed < self.base_cube.channels:
                try:
                    updates.get(timeout=0.5)
                    completed += 1
                    print(f"Completed {completed}/{self.base_cube.channels} layers")
                except queue.Empty:
                    pass

            wait(futures)

    def stitch_datacubes(self) -> DatacubeFragment:
        if (len(self.fragments) != len(self.points)):
            raise ValueError("Number of images must match number of point sets.")

        if (self.base_cube.is_spectral()):
            datacube_file = "stitched_spectral.raw"
            rpl_file = "stitched_spectral.rpl"
            print("Estimated file size is:", (self.scaled_width * self.scaled_height * self.base_cube.channels)/(1024**3), "GB")
            return SpectralDatacubeFragment.write_file(
                datacube_file,
                rpl_file,
                self.base_cube.rpl_meta,
                self.base_cube.data_type,
                self.scaled_width,
                self.scaled_height,
                self.base_cube.channels,
                lambda output_map:
                    self.fill_layers(output_map)
            )
        else:
            datacube_file = "stitched_elemental.dms"
            return ElementalDatacubeFragment.write_file(
                datacube_file,
                self.scaled_width,
                self.scaled_height,
                self.base_cube.channels,
                self.base_cube.elements,
                lambda output_map:
                    self.fill_layers(output_map)       
            )

    def get_perspective_matrices(self) -> list[np.ndarray]:
        perspective_matrices = []
        for i, (src, dst) in enumerate(self.points):
            perspective_matrice = cv.getPerspectiveTransform(src.get_points(), dst.get_points(self.scalar))    
            perspective_matrices.append(perspective_matrice)
        return perspective_matrices

class WarpSelection:

    def __init__(self, top_left: tuple[int, int], top_right: tuple[int, int], bottom_left: tuple[int, int], bottom_right: tuple[int, int]):
        self.top_left = top_left
        self.top_right = top_right
        self.bottom_left = bottom_left
        self.bottom_right = bottom_right

    def get_points(self, scalar: float = 1.0) -> np.ndarray:
        if (scalar != 1.0):
            return np.array([
                (int(self.top_left[0] * scalar), int(self.top_left[1] * scalar)),
                (int(self.top_right[0] * scalar), int(self.top_right[1] * scalar)),
                (int(self.bottom_left[0] * scalar), int(self.bottom_left[1] * scalar)),
                (int(self.bottom_right[0] * scalar), int(self.bottom_right[1] * scalar))
            ], dtype=np.float32)
        else:
            return np.array([self.top_left, self.top_right, self.bottom_left, self.bottom_right], dtype=np.float32)

class Dimensions:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

class DatacubeFragment(ABC):
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
        pass

    @abstractmethod
    def load_datacube(self) -> np.memmap:
        pass

    @abstractmethod
    def is_spectral(self) -> bool:
        pass

    def export_projection(self, file: str) -> None:
        picture = self.create_greyscale_projection()
        plt.imsave(file, picture, cmap="gray", format="jpg", vmin=picture.min(), vmax=picture.max())

    def create_greyscale_projection(self, chunk_size: int =256) -> np.ndarray:
        memmap = self.load_datacube()
        out = np.zeros((self.height, self.width), dtype=np.float32)
        if self.is_spectral():
            for y0 in range(0, self.height, chunk_size):
                y1 = min(y0 + chunk_size, self.height)
                print("Reducing chunk rows", y0, "to", y1, "of", self.height)
                chunk = memmap[y0:y1, :, :]
                out[y0:y1, :] = chunk.mean(axis=2).astype(np.float32)
                memmap.flush()
        else:
            acc = np.zeros((self.height, self.width), dtype=np.float32)
            for c0 in range(0, self.channels, chunk_size):
                c1 = min(c0 + chunk_size, self.channels)
                print("Reducing chunk channels", c0, "to", c1, "of", self.channels)
                chunk_data = memmap[c0:c1, :, :]
                acc += chunk_data.sum(axis=0)
            out[:, :] = (acc / self.channels).astype(np.float32)
        return out

class ElementalDatacubeFragment(DatacubeFragment):
    def __init__(self, datacube_file: str, width: int, height: int, channels: int, offset: int, rotation: int, elements: list[str]):
        super().__init__(datacube_file, width, height, channels, rotation)
        self.offset = offset
        self.elements = elements

    @classmethod
    def from_file(cls, datacube_file: str, rotation: int = 0):
        with open(datacube_file, "rb") as file:
            file.readline()
            dimensions_list = file.readline().decode("ascii").strip().split()
            width, height, channels = [int(dim) for dim in dimensions_list]
            header_size = file.tell()
            file.seek(width * height * channels * 4, 1)
            elements = []
            for _ in range(channels):
                elements.append(file.readline().decode("ascii").strip())
        return cls(datacube_file, width, height, channels, header_size, rotation, elements)
        
    def load_datacube(self) -> np.memmap:
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
        return self.channels == datacube.channels and np.array_equal(self.elements, datacube.elements)

    @staticmethod
    def write_file(datacube_file: str, width: int, height: int, channels:int, elements: list[str], content_write_function: Callable[[np.ndarray]]) -> ElementalDatacubeFragment:
        header = ElementalDatacubeFragment.create_file_header(width, height, channels)
        with open(datacube_file, "wb") as f:
            f.write(header)
        output_map = np.memmap(
            datacube_file,
            dtype=np.float32,
            offset=len(header),
            mode="r+",
            shape=(channels, height, width),
        )
        content_write_function(output_map)
        output_map.flush()
        footer = ElementalDatacubeFragment.create_file_footer(elements)
        with open(datacube_file, "ab") as f:
            f.write(footer)
        return ElementalDatacubeFragment.from_file(datacube_file)

    @staticmethod
    def create_file_header(width: int, height: int, channels:int) -> bytes:
        header_lines = [
            "2\n",
            f"{width:10d}{height:10d}{channels:11d}\n"
        ]
        return  "".join(header_lines).encode("ascii")

    @staticmethod
    def create_file_footer(elements: list[str]) -> bytes:
        footer_text = "\r\n".join(elements) + "\r\n"
        return footer_text.encode("ascii")
    
    def is_spectral(self):
        return False

class SpectralDatacubeFragment(DatacubeFragment):
    def __init__(self, datacube_file: str, width: int, height: int, channels: int, offset: int, data_type, rotation: int, rpl_meta: dict):
        super().__init__(datacube_file, width, height, channels, rotation)
        self.offset = offset
        self.data_type = data_type
        self.rpl_meta = rpl_meta
    @classmethod
    def from_file(cls, datacube_file: str, rpl_file: str, rotation: int = 0):
        is_reshaped = datacube_file.endswith(".reshaped")
        meta = cls.parse_rpl_file(rpl_file)
        width = meta.get("width", 0)
        height = meta.get("height", 0)
        channels = meta.get("depth", 0)
        offset = meta.get("offset", 0)
        data_len = meta.get("data-Length", 0)
        if data_len not in (1, 2, 4, 8):
            raise ValueError(f"Unsupported element size: {data_len} bytes")
        data_order = meta.get("byte-order")
        data_type = meta.get("data-type")
        dtype_signed = "u" if data_type == "unsigned" else "i"
        dtype_order = ">" if data_order == "big-endian" else "<"
        dtype = f"{dtype_order}{dtype_signed}{data_len}"
        return cls(datacube_file, width, height, channels, offset, dtype, rotation, meta)

    @classmethod
    def parse_rpl_file(cls, rpl_file: str) -> dict:
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
        print("Loading spectral datacube:", self.datacube_file)
        memmap: np.memmap = np.memmap(
                self.datacube_file,
                dtype=self.data_type,
                mode="r",
                offset=self.offset,
                shape=(self.height, self.width, self.channels),
            )
        return memmap

    def are_compatible(self, datacube) -> bool:
        if not isinstance(datacube, SpectralDatacubeFragment):
            return False
        return self.channels == datacube.channels and self.data_type == datacube.data_type

    @staticmethod
    def write_rpl_file(rpl_file: str, rpl_meta: dict, width: int, height: int) -> None:
        rpl_meta = rpl_meta.copy()
        rpl_meta["width"] = width
        rpl_meta["height"] = height
        rpl_meta["offset"] = 0
        with open(rpl_file, "w") as f:
            for key, value in rpl_meta.items():
                f.write(f"{key:<12}\t{value}\n")

    @staticmethod
    def write_file(datacube_file: str, rpl_file: str, rpl_meta: dict, data_type: str, width: int, height: int, channels:int, content_write_function: Callable[[np.memmap]]) -> SpectralDatacubeFragment:
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