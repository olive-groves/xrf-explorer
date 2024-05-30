import json
import logging
from os.path import join, normpath, abspath
from pathlib import Path

import PIL
from PIL.Image import Image

from xrf_explorer.server.file_system.config_handler import load_yml

LOG: logging.Logger = logging.getLogger(__name__)


def get_contextual_image_path(data_source: str, name: str, config_path: str = "config/backend.yml") -> str | None:
    """
    Returns the path of the requested contextual image. If no file is found, it will return None. This will
also happen if the config file is empty.
    :param config_path: The path to the config file.
    :param data_source: The data source to fetch the image from.
    :param name: The name of the image. Must be present in workspace.json for the data source as the base image or a
contextual image.
    :return: The path to the file.
    """

    LOG.info("Searching for contextual image %s in data source %s.", name, data_source)

    # Find the folder where the contextual image is stored.
    backend_config: dict = load_yml(config_path)
    if not backend_config:
        LOG.error("Config file is empty.")
        return None

    data_source_dir = join(Path(backend_config["uploads-folder"]), data_source)
    workspace_path = join(data_source_dir, "workspace.json")
    try:
        with open(workspace_path, 'r') as workspace:
            data_json: str = workspace.read()
            data = json.loads(data_json)
            if data["baseImage"]["name"] == name:
                return abspath(join(data_source_dir, data["baseImage"]["imageLocation"]))
            else:
                for image in data["contextualImages"]:
                    if image["name"] == name:
                        return abspath(join(data_source_dir, image["imageLocation"]))
    except OSError as err:
        LOG.error("Error while getting elemental cube name: %s", err)

    return None


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
