import numpy as np
import csv
from cv2 import (
    imread,
    imwrite,
    IMREAD_UNCHANGED,
    warpPerspective,
    getPerspectiveTransform,
    INTER_AREA,
    resize,
)

from numpy._typing import NDArray
from cv2.typing import MatLike
from xrf_explorer.server.file_system.from_dms import (
    get_elemental_datacube_dimensions_from_dms,
)


def load_image_toregister(path_image_toregister: str) -> MatLike:
    """Loads an image from the specified path. Handles PNGs with alpha channels specially."""

    if path_image_toregister.endswith(".png"):  # Preserve the alpha channel if a PNG.
        image_toregister = imread(path_image_toregister, IMREAD_UNCHANGED)
        if (
            image_toregister.ndim == 2
        ):  # ...but if the PNG is monochannel, redo the imread and let cv2 determine how.
            image_toregister = imread(path_image_toregister)
    else:
        image_toregister = imread(path_image_toregister)

    return image_toregister


def resize_image_register(
    image_register: MatLike, image_reference_height: int, image_reference_width: int
) -> MatLike:
    """Resizes an image to fit the reference image's aspect ratio."""

    image_register_height, image_register_width = image_register.shape[:2]

    aspect_reference = image_reference_width / image_reference_height  # W/H (e.g., 4:3)
    aspect_toregister = image_register_width / image_register_height  # w/h (e.g., 16:9)

    image_toregister_resize_width = None
    image_toregister_resize_height = None

    if aspect_toregister > aspect_reference:
        # If the toregister is wider than the reference, resize toregister to match widths
        image_toregister_resize_width = image_reference_width
        image_toregister_resize_height = int(image_reference_width / aspect_toregister)
    else:
        # If the toregister is narrower or equi-aspect to the reference, resize toregister to match heights
        image_toregister_resize_height = image_reference_height
        image_toregister_resize_width = int(
            image_toregister_resize_height * aspect_toregister
        )

    return resize(
        image_register,
        (image_toregister_resize_width, image_toregister_resize_height),
        interpolation=INTER_AREA,
    )


def pad_image_register(
    image_register: MatLike, image_reference_height: int, image_reference_width: int
) -> MatLike:
    """Pads the image to match the size of the reference image."""

    image_register_height, image_register_width = image_register.shape[:2]

    # NOTE: either add_rows or add_cols must be 0, since the resizing matches either the height or the width of the image to be image_registered
    add_rows = image_reference_height - image_register_height
    add_cols = image_reference_width - image_register_width

    if image_register.ndim == 2:
        return np.pad(image_register, ((0, add_rows), (0, add_cols)), "constant")
    else:
        return np.pad(
            image_register,
            ((0, add_rows), (0, add_cols), (0, 0)),
            "constant",
        )


def apply_prespective_transformation(
    image: MatLike, points_src: NDArray[np.float32], points_dest: NDArray[np.float32]
) -> MatLike:
    """Applies a perspective transformation based on source and destination points."""

    image_height, image_width = image.shape[:2]

    transform = getPerspectiveTransform(points_src, points_dest)

    return warpPerspective(image, transform, (image_width, image_height))


def load_points(
    path_points_csv_file: str,
) -> tuple[NDArray[np.float32], NDArray[np.float32]]:
    """Loads control points for the transformation from a CSV file."""

    points_source: list[list[np.float32]] = []
    points_destination: list[list[np.float32]] = []

    with open(path_points_csv_file, "r", newline="") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter="|")
        points_list = list(csv_reader)[-4:]

        for row in points_list:
            row = [np.float32(el) for el in row]
            points_source.append(row[2:])
            points_destination.append(row[:2])

    return np.array(points_source), np.array(points_destination)


def register_image_to_image(
    path_image_reference: str,
    path_image_register: str,
    path_csv_points: str,
    path_result_registered_image: str,
):
    image_reference = imread(path_image_reference)
    image_register = load_image_toregister(path_image_register)

    image_reference_height, image_reference_width = image_reference.shape[:2]

    image_register_resize = resize_image_register(
        image_register, image_reference_height, image_reference_width
    )

    image_register_pad = pad_image_register(
        image_register_resize, image_reference_height, image_reference_width
    )
    points_source, points_destination = load_points(path_csv_points)
    image_registered = apply_prespective_transformation(
        image_register_pad, points_source, points_destination
    )

    _ = imwrite(path_result_registered_image, image_registered)


def register_image_to_data_cube(
    path_data_cube: str, path_image_register: str, path_result_registered_image
):
    cube_w, cube_h, _, _ = get_elemental_datacube_dimensions_from_dms(path_data_cube)
    image_register = imread(path_image_register)
    image_resized = resize(image_register, (cube_w, cube_h))

    _ = imwrite(path_result_registered_image, image_resized)
