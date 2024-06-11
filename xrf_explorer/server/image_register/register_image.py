import numpy as np
from os.path import exists, dirname
import logging
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

from numpy.typing import NDArray
from cv2.typing import MatLike
from xrf_explorer.server.file_system import (
    get_elemental_cube_path, get_elemental_cube_recipe_path, 
    get_contextual_image_path, get_contextual_image_recipe_path, get_contextual_image_size, 
    get_path_to_base_image, is_base_image
)
from xrf_explorer.server.file_system.from_dms import (
    get_elemental_datacube_dimensions_from_dms,
)

LOG: logging.Logger = logging.getLogger(__name__)


def load_image_toregister(path_image_toregister: str) -> MatLike | None:
    """Loads an image from the specified path. Preserves the alpha channel of .png files.
    
    :param path_image_toregister: Path of the image to be loaded for registering.
    :return: A MatLike representation of the image. If the image cannot be read, it returns None
    """

    if path_image_toregister.endswith(".png"):  # Preserve the alpha channel if a PNG.
        image_toregister = imread(path_image_toregister, IMREAD_UNCHANGED)
        if (
                image_toregister.ndim == 2
        ):  # ...but if the PNG is monochannel, redo the imread and let cv2 determine how.
            image_toregister = imread(path_image_toregister)
    else:
        image_toregister = imread(path_image_toregister)

    if image_toregister is None:
        LOG.error("Image could not be loaded.")

    return image_toregister


def resize_image_fit_aspect_ratio(
        image_resize: MatLike, image_reference_height: int, image_reference_width: int
) -> MatLike:
    """Resizes an image to the aspect ratio calculated by the reference image width
    and height (image_reference_width, image_reference_height).

    :param image_resize: A MatLike representation of the image to be resized.
    :param image_reference_height: The height of the reference image (in number of pixels).
    :param image_reference_width: The width of the reference image (in number of pixels).
    :return: A MatLike representation of the resized image.
    """

    image_register_height, image_register_width = image_resize.shape[:2]

    aspect_reference: float = image_reference_width / image_reference_height  # W/H (e.g., 4:3)
    aspect_to_register: float = image_register_width / image_register_height  # w/h (e.g., 16:9)

    image_to_register_resize_width: int
    image_to_register_resize_height: int

    if aspect_to_register > aspect_reference:
        # If the to_register is wider than the reference, resize to_register to match widths
        image_to_register_resize_width = image_reference_width
        image_to_register_resize_height = int(image_reference_width / aspect_to_register)
    else:
        # If the to_register is narrower or equi-aspect to the reference, resize to_register to match heights
        image_to_register_resize_height = image_reference_height
        image_to_register_resize_width = int(
            image_to_register_resize_height * aspect_to_register
        )

    return resize(
        image_resize,
        (image_to_register_resize_width, image_to_register_resize_height),
        interpolation=INTER_AREA,
    )


def pad_image_to_match_size(
        image_to_pad: MatLike, image_reference_height: int, image_reference_width: int
) -> MatLike:
    """Pads the image or removes padding to match the size of the reference image.

    :param image_to_pad: A MatLike representation of the image to be padded.
    :param image_reference_height: The height of the reference image.
    :param image_reference_width: The width of the reference image.
    :return: A MatLike representation of the padded image.
    """

    image_register_height, image_register_width = image_to_pad.shape[:2]

    # Get the difference between the reference and the image to pad
    row_difference: int = image_reference_height - image_register_height
    col_difference: int = image_reference_width - image_register_width

    # Remove padding from the image
    image_without_padding: MatLike = image_to_pad

    if col_difference < 0:
        LOG.info(f"Removing columns: {-col_difference}")
        
        image_without_padding = image_to_pad[:, :image_reference_width]
    if row_difference < 0:
        LOG.info(f"Removing rows: {-row_difference}")

        image_without_padding = image_to_pad[:image_reference_height, :] 

    # Add padding to the image
    add_rows = max(0, row_difference)
    add_cols = max(0, col_difference)

    LOG.info(f"Adding rows and columns: ({add_rows}, {add_cols})")

    if image_without_padding.ndim == 2:
        return np.pad(image_without_padding, ((0, add_rows), (0, add_cols)), "constant")
    else:
        return np.pad(
            image_without_padding,
            ((0, add_rows), (0, add_cols), (0, 0)),
            "constant",
        )


def apply_perspective_transformation(
        image_to_transform: MatLike, points_src: MatLike, points_dest: MatLike
) -> MatLike:
    """Applies a perspective transformation on an image based on source and destination points.
    :param image_to_transform: A MatLike representation of the image to be transformed.
    :param points_src: A MatLike representation of the source points.
    :param points_dest: A MatLike representation of the destination points.
    """

    image_height, image_width = image_to_transform.shape[:2]

    transform = getPerspectiveTransform(points_src, points_dest)

    return warpPerspective(image_to_transform, transform, (image_width, image_height))


def load_points(
        path_points_csv_file: str,
) -> tuple[NDArray[np.float32], NDArray[np.float32]]:
    """Loads the control points for the transformation from a CSV file, as generated by the
    butterfly_registrator

    :param path_points_csv_file: Path of the csv file.
    :return: A tuple containing a numpy array with the source points at index 0 and a
    numpy array with the destination points at index 1.
    """

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


def load_points_dict(path_points_csv_file: str) -> dict[str, list[np.float32]] | None:
    """Loads the control points for the transformation from a CSV file, as generated by the
    butterfly_registrator

    :param path_points_csv_file: Path of the csv file.
    :return: A dict containing the registration points.
    """

    # Get the recipe points
    points: tuple[NDArray[np.float32], NDArray[np.float32]] = load_points(path_points_csv_file)
    if not points:
        return None

    # Convert the points to a nice format
    points_dict: dict = {
        "moving": points[0].tolist(),
        "target": points[1].tolist()
    }

    return points_dict


def register_image(
        image: MatLike, 
        new_width: int, new_height: int, 
        points_source: np.ndarray, points_destination: np.ndarray
) -> MatLike:
    """Register the given image to match the new width and height with transformation given by the source and destination points.

    :param image: The image to be registered.
    :param new_width: The new width of the image.
    :param new_height: The new height of the image.
    :param points_source: The source points.
    :param points_destination: The destination points.
    :return: The registered image.
    """

    resized_image: MatLike = resize_image_fit_aspect_ratio(image, new_height, new_width)

    padded_image: MatLike = pad_image_to_match_size(resized_image, new_height, new_width)

    return apply_perspective_transformation(padded_image, points_source, points_destination)


def inverse_register_image(
        image: MatLike, 
        new_width: int, new_height: int, 
        points_source: np.ndarray, points_destination: np.ndarray
) -> MatLike:
    """Inverse register the given image to match the new width and height with transformation given by the source and destination points.

    :param image: The image to be registered.
    :param new_width: The new width of the image.
    :param new_height: The new height of the image.
    :param points_source: The source points.
    :param points_destination: The destination points.
    :return: The inverse registered image.
    """

    # Inverse transform the image, this is done by swapping the source and destination points in the method
    image_transformed: MatLike = apply_perspective_transformation(image, points_destination, points_source)
    
    # Get the dimensions of the image
    image_height, image_width = image_transformed.shape[:2]

    # Calculate the aspect ratios
    aspect_image: float = image_width / image_height
    aspect_registered_image: float = new_width / new_height

    # Remove the padding, either rows or columns from the bottom or right
    image_without_padding: MatLike

    if aspect_image > aspect_registered_image:
        # Height is scaled to match the cube
        # So columns are added to match the width, which we have to remove
        scaled_width: int = int(new_width * image_height / new_height)
        image_without_padding = pad_image_to_match_size(image_transformed, image_height, scaled_width)

    else:
        # Width is scaled to match the cube
        # So rows are added to match the height, which we have to remove
        scaled_height: int = int(new_height * image_width / new_width)
        image_without_padding = pad_image_to_match_size(image_transformed, scaled_height, image_width)

    # Scale image down to match the cube
    return resize(
        image_without_padding,
        (new_width, new_height),
        interpolation=INTER_AREA,
    )


def register_image_to_image(
        path_image_reference: str,
        path_image_register: str,
        path_csv_points: str,
        path_result_registered_image: str,
) -> bool:
    """
    Registers an image to align with a reference image by resizing, padding, and applying
    perspective transformation. It uses control points from a CSV, generated by the butterfly_registrator,
    to apply the perspective transformation.

    :param path_image_reference: The path of the reference image.
    :param path_image_register: The path of the image to be registered.
    :param path_csv_points: The path of the .csv file.
    :param path_result_registered_image: The path where the registered image will be uploaded to.
    :return: True if the registered image has been written to the specified path successfully and false otherwise.
    """

    image_reference = imread(path_image_reference)
    image_register = load_image_toregister(path_image_register)

    if image_reference is None:
        LOG.error("Reference image could not be loaded")
        return False

    if image_register is None:
        LOG.error("Image for registering could not be loaded")
        return False

    if not exists(path_csv_points):
        LOG.error(f"Control points file could not be found at {path_csv_points}")
        return False

    path_result_dirname = dirname(path_result_registered_image)
    if not exists(path_result_dirname):
        LOG.error(
            f"Registered image could not be saved at {path_result_dirname} because directory does not exist."
        )
        return False

    image_reference_height, image_reference_width = image_reference.shape[:2]
    
    points_source, points_destination = load_points(path_csv_points)
    
    registered_image: MatLike = register_image(
        image_register, image_reference_width, image_reference_height, points_source, points_destination
    )

    return imwrite(path_result_registered_image, registered_image)


def get_image_registered_to_data_cube(data_source: str, image_name: str) -> MatLike | None:
    """
    Registers an image to align with the dimensions of the data cube.

    :param data_source: The name of the data source.
    :param image_name: The name of the image to be registered.
    :return: The registered image or None in case of an error.
    """

    # Get the data cube and check if the data cube exists
    path_data_cube: str | None = get_elemental_cube_path(data_source)
    if path_data_cube is None:
        LOG.error(f"Data cube not found at {path_data_cube}")
        return None
    
    # Load the data cube dimensions
    cube_w, cube_h, _, _ = get_elemental_datacube_dimensions_from_dms(path_data_cube)
    
    # Get the path to the image to be registered
    path_image_register: str | None = get_contextual_image_path(data_source, image_name)
    if path_image_register is None:
        LOG.error(f"Image for registering not found at {path_image_register}")
        return None
    
    # Load the image to be registered
    image_register: MatLike = imread(path_image_register)
    if image_register is None:
        LOG.error(f"Image for registering not found at {path_image_register}")
        return None
    
    # Check if the image is the base image
    is_image_base_image: bool | None = is_base_image(data_source, image_name)
    if is_image_base_image is None:
        return None

    # If not base image, register image to base image first
    if not is_image_base_image:
        # Get recipe to base image
        base_recipe_path: str | None = get_contextual_image_recipe_path(data_source, image_name)
        if base_recipe_path is None:
            return None 
        
        # Load the control points and apply the perspective transformation
        points_source, points_destination = load_points(base_recipe_path)

        # Get path to base image
        path_to_base_image: str | None = get_path_to_base_image(data_source)
        if path_to_base_image is None:
            return None

        # Get the size of the base image
        base_image_size: tuple[int, int] | None = get_contextual_image_size(path_to_base_image)
        if base_image_size is None:
            return None
        
        base_image_width, base_image_height = base_image_size

        # Register the image to the base image
        LOG.info("Registering image to base image")
        
        image_register = register_image(
            image_register, base_image_width, base_image_height, points_source, points_destination
        )

    # Get elemental data cube recipe
    cube_recipe_path: str | None = get_elemental_cube_recipe_path(data_source)
    if cube_recipe_path is None:
        return None
    
    # Load the control points and apply the perspective transformation
    points_source, points_destination = load_points(cube_recipe_path)
    
    # Inverse register the image 
    LOG.info("Registering image to elemental cube")
    
    return inverse_register_image(image_register, cube_w, cube_h, points_source, points_destination)
