import logging

import json
from os.path import join, abspath
from pathlib import Path

import PIL
from PIL.Image import Image

from xrf_explorer.server.file_system.config_handler import get_config

LOG: logging.Logger = logging.getLogger(__name__)


def get_contextual_image_data(data_source: str, name: str) -> dict | None:
    """
    Returns a contextual image from workspace.json. Returns None if the image or data_source does not exist.
    :param data_source: The data source to fetch the image from.
    :param name: The name of the image. Must be present in workspace.json for the data source as the base image or a
contextual image.
    :return: Dict containing the name, imageLocation and recipeLocation of a contextual image.
    """

    LOG.info("Searching for contextual image %s in data source %s.", name, data_source)

    # Find the folder where the contextual image is stored.
    backend_config: dict = get_config()
    if not backend_config:
        LOG.error("Config file is empty.")
        return None

    data_source_dir: str = join(backend_config["uploads-folder"], data_source)
    workspace_path: str = join(data_source_dir, "workspace.json")
    try:
        with open(workspace_path, 'r') as workspace:
            data_json: str = workspace.read()
            data: dict = json.loads(data_json)
            if data["baseImage"]["name"] == name:
                return data["baseImage"]
            else:
                for image in data["contextualImages"]:
                    if image["name"] == name:
                        return image
    except OSError as err:
        LOG.error("Error while getting contextual image: %s", err)

    LOG.error("Could not find contextual image %s in source %s", name, data_source)
    return None


def get_contextual_image_path(data_source: str, name: str) -> str | None:
    """
    Returns the path of the requested contextual image. If no file is found, it will return None. This will
also happen if the config file is empty.
    :param data_source: The data source to fetch the image from.
    :param name: The name of the image. Must be present in workspace.json for the data source as the base image or a
contextual image.
    :return: The path to the file.
    """

    # Get the contextual image
    image: dict = get_contextual_image_data(data_source, name)
    if not image:
        return None

    # Find the folder where the contextual image is stored.
    backend_config: dict = get_config()
    if not backend_config:
        LOG.error("Config file is empty.")
        return None

    return abspath(join(Path(backend_config["uploads-folder"]), data_source, image["imageLocation"]))


def get_contextual_image_recipe_path(data_source: str, name: str) -> str | None:
    """
    Returns the path of the registering recipe of the requested contextual image. If no file is found, it will return
None. This will also happen if the config file is empty.
    :param data_source: The data source to fetch the image from.
    :param name: The name of the image. Must be present in workspace.json for the data source as the base image or a
contextual image.
    :return: The path to the file.
    """

    # Get the contextual image
    image: dict = get_contextual_image_data(data_source, name)
    if not image:
        return None

    location: str = image["recipeLocation"]
    if not location:
        LOG.error("Image %s in source %s has no configured recipe location.", name, data_source)
        return None

    # Find the folder where the contextual image is stored.
    backend_config: dict = get_config()
    if not backend_config:
        LOG.error("Config file is empty.")
        return None

    return abspath(join(Path(backend_config["uploads-folder"]), data_source, location))


def get_contextual_image(image_path: str) -> Image | None:
    """Open and returns an image at a specified path.

    :param image_path: The path to the image file.
    :return: The image.
    """

    try:
        return PIL.Image.open(image_path)
    except FileNotFoundError as err:
        LOG.error("Image file %s not found: %s", image_path, err)
    except PIL.UnidentifiedImageError as err:
        LOG.error("PIL could not open %s: %s", image_path, err)

    return None


def get_contextual_image_size(image_path: str) -> tuple[int, int] | None:
    """Get the size of an image.

    :param image_path: The path to the image file.
    :return: The dimensions of the image.
    """

    image: Image = get_contextual_image(image_path)
    if not image:
        return None

    return image.size
