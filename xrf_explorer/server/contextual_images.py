import logging
import os
import shutil
from os.path import join, normpath

from xrf_explorer.server.file_system.config_handler import load_yml

allowed_formats: set = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'}
LOG: logging.Logger = logging.getLogger(__name__)


def set_contextual_image(path_to_image: str):
    """
    Saves a copy of the input file to contextual image folder.
    Allowed file types are ".png", ".jpg", ".jpeg", ".bmp", ".tiff" and ".tif".
    :param path_to_image: The path to the image that needs to be copied.
    """

    LOG.info("Saving contextual image.")

    # Find the folder where the contextual image is stored.
    backend_config: dict = load_yml("config/backend.yml")
    if not backend_config:
        LOG.error("Config file is empty.")
        return
    folder: str = backend_config["contextual-images-folder"]

    # Check if the input file actually exists.
    if not os.path.isfile(path_to_image):
        LOG.error(f"The file at path {path_to_image} does not exist.")
        return

    # Get file extension.
    file_extension: str = path_to_image.split('.')[-1]

    # Convert file type to lower case and ensure it starts with a period.
    file_extension: str = f".{file_extension.lower()}" if not file_extension.startswith('.') else file_extension.lower()

    # Check if extension is valid. If not, return.
    if file_extension not in allowed_formats:
        LOG.error("The provided file has an invalid type.")
        return

    # Construct the destination path.
    destination_path: str = os.path.join(folder, f"contextual_image{file_extension}")

    # Copy the image to the destination path
    shutil.copy(path_to_image, destination_path)

    LOG.info("Contextual image saved successfully.")


def get_contextual_image(file_type: str) -> str:
    """
    Returns the path of the contextual image with the provided file type. If no file is found, it will return the empty
    string. This will also happen if the provided file type is not allowed or if the config file is empty.
    :param file_type: The type of the file to get the path of. Allowed file types are ".png", ".jpg", ".jpeg", ".bmp",
            ".tiff" and ".tif".
    :return: The path to the file.
    """

    LOG.info("Searching for contextual image.")

    # Find the folder where the contextual image is stored.
    backend_config: dict = load_yml("config/backend.yml")
    if not backend_config:
        LOG.error("Config file is empty.")
        return ""
    folder: str = backend_config["contextual-images-folder"]

    # Convert file type to lower case and ensure it starts with a period.
    file_extension: str = f".{file_type.lower()}" if not file_type.startswith('.') else file_type.lower()

    # Check if the file type is in an allowed format.
    if file_extension not in allowed_formats:
        LOG.error("The provided file type is invalid.")
        return ""

    # Construct the file path.
    file_path: str = normpath(join(folder, f"contextual_image{file_extension}"))

    # Check if the file exists and if so, return it.
    if os.path.isfile(file_path):
        LOG.info("Contextual image found.")
        return file_path
    else:
        LOG.error("File was not found.")
        return ""
