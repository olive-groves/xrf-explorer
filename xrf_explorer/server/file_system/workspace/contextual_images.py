import json
import logging

from os.path import join, abspath
from pathlib import Path

import PIL

from PIL.Image import Image

from xrf_explorer.server.file_system import get_config
from xrf_explorer.server.file_system.workspace.file_access import get_workspace_dict

LOG: logging.Logger = logging.getLogger(__name__)

# Remove the safety limit on max pixels, since some contextual images 
# are above the limit
PIL.Image.MAX_IMAGE_PIXELS = None


def get_contextual_image_data(data_source: str, name: str) -> dict | None:
    """Returns a contextual image from workspace.json. Returns None if the image or data_source does not exist.

    :param data_source: The data source to fetch the image from
    :param name: The name of the image. Must be present in workspace.json for the data source as the base image or a contextual image
    :return: Dict containing the name, imageLocation and recipeLocation of a contextual image
    """

    LOG.info("Searching for contextual image %s in data source %s.", name, data_source)

    # Find the folder where the contextual image is stored.
    backend_config: dict = get_config()
    if not backend_config:
        LOG.error("Config file is empty.")
        return None

    # load workspace dict
    workspace: dict = get_workspace_dict(data_source)
    if not workspace:
        LOG.error("Could not get contextual image for project %s", data_source)
        return None

    # find contextual image
    if workspace["baseImage"]["name"] == name:
        return workspace["baseImage"]
    for image in workspace["contextualImages"]:
        if image["name"] == name:
            return image

    LOG.error("Could not find contextual image %s in source %s", name, data_source)
    return None


def get_contextual_image_path(data_source: str, name: str) -> str | None:
    """Returns the path of the requested contextual image. If no file is found, it will return None. This will also
    happen if the config file is empty.

    :param data_source: The data source to fetch the image from
    :param name: The name of the image. Must be present in `workspace.json` for the data source as the base image or a contextual image
    :return: The path to the requested contextual image
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
    """Returns the path of the registering recipe of the requested contextual image. If no file is found, it will return
    None. This will also happen if the config file is empty.

    :param data_source: The data source to fetch the image from
    :param name: The name of the image. Must be present in `workspace.json` for the data source as the base image or a contextual image
    :return: The path to the recipe of the requested contextual image
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

    :param image_path: The path to the image file
    :return: The image
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

    :param image_path: The path to the image file
    :return: The dimensions of the image
    """

    image: Image = get_contextual_image(image_path)
    if not image:
        return None

    return image.size


def get_base_image_name(data_source: str) -> str | None:
    """Get the name to the base image of the data source.
    
    :param data_source: The data source to get the base image from
    :return: The name of the base image
    """

    LOG.info("Getting path to base image of data source %s.", data_source)

    # Find the folder where the contextual image is stored.
    backend_config: dict = get_config()
    if not backend_config:
        LOG.error("Config file is empty.")
        return None

    workspace: dict = get_workspace_dict(data_source)
    try:
        return workspace["baseImage"]["name"]
    except KeyError:
        LOG.error(f"Could not parse the workspace for project {data_source}")

    return None


def get_path_to_base_image(data_source: str) -> str | None:
    """Get the path to the base image of the data source.
    
    :param data_source: The data source to get the base image from
    :return: The path to the base image
    """

    # Get the name of the base image
    base_image_name: str | None = get_base_image_name(data_source)
    if base_image_name is None:
        return None

    # Return the path to the base image
    return get_contextual_image_path(data_source, base_image_name)


def is_base_image(data_source: str, name: str) -> bool | None:
    """Check if the image is the base image of the data source.

    :param data_source: The data source to check whether the name is the base image
    :param name: The name of the image. Must be present in workspace.json for the data source as the base image or a contextual image
    :return: True if the image is the base image, False otherwise
    """

    # Get the name of the base image
    base_image_name: str | None = get_base_image_name(data_source)
    if base_image_name is None:
        return None

    # Return whether the name is the base image
    return base_image_name == name
