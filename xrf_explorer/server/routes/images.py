from io import BytesIO
from logging import Logger, getLogger

from PIL.Image import Image
from flask import send_file

from xrf_explorer import app

from xrf_explorer.server.file_system.workspace import (
    get_contextual_image_path,
    get_contextual_image,
    get_contextual_image_size,
    get_contextual_image_recipe_path
)
from xrf_explorer.server.file_system import get_config
from os.path import abspath, join
from os.path import isfile
from pathlib import Path

from xrf_explorer.server.image_register import load_points_dict

LOG: Logger = getLogger(__name__)


def _resolve_image_path(data_source: str, name: str) -> str | None:
    """
    Resolve an image name to an absolute path. Accepts either a workspace image name
    or a path-like name (e.g. "generated/..."). Returns the absolute path or None
    if it cannot be resolved.
    """
    # path-like names are treated as direct paths under the uploads-folder
    if "/" in name:
        backend_config = get_config()
        if not backend_config:
            return None
        path = abspath(join(Path(backend_config["uploads-folder"]), data_source, name))
        return path

    # otherwise resolve via workspace lookup
    path = get_contextual_image_path(data_source, name)
    return path


@app.route("/api/<data_source>/image/<path:name>")
def contextual_image(data_source: str, name: str):
    """
    Get a contextual image.

    :param data_source: data source to get the image from
    :param name: the name of the image in `workspace.json`
    :return: the contextual image converted to png
    """

    # Resolve the path and log for debugging
    path = _resolve_image_path(data_source, name)
    LOG.info("Resolved image path for %s (data source %s): %s", name, data_source, path)
    if not path or not isfile(path):
        LOG.info("Image file exists check for %s: %s", path, False)
        return f"Image {name} not found in source {data_source}", 404
    LOG.info("Image file exists check for %s: %s", path, True)

    LOG.info("Opening contextual image")

    image: Image | None = get_contextual_image(path)
    if image is None:
        return f"Failed to open image {name} from source {data_source}", 500

    LOG.info("Converting contextual image")

    image_io = BytesIO()
    image.save(image_io, "png")
    image_io.seek(0)

    LOG.info("Serving converted contextual image")

    # Ensure that the converted images are cached by the client
    response = send_file(image_io, mimetype='image/png')
    response.headers["Cache-Control"] = "public, max-age=604800, immutable"
    return response


@app.route("/api/<data_source>/image/<path:name>/size")
def contextual_image_size(data_source: str, name: str):
    """
    Get the size of a contextual image.

    :param data_source: data source to get the image from
    :param name: the name of the image in `workspace.json`
    :return: the size of the contextual image
    """

    path = _resolve_image_path(data_source, name)
    LOG.info("Resolved image path for size request %s (data source %s): %s", name, data_source, path)
    if not path or not isfile(path):
        LOG.info("Image file exists check for size %s: %s", path, False)
        return f"Image {name} not found in source {data_source}", 404
    LOG.info("Image file exists check for size %s: %s", path, True)

    size: tuple[int, int] | None = get_contextual_image_size(path)
    if not size:
        return f"Failed to get size of image {name} from source {data_source}", 500

    return {
        "width": size[0],
        "height": size[1]
    }


@app.route("/api/<data_source>/image/<path:name>/recipe")
def contextual_image_recipe(data_source: str, name: str):
    """
    Get the registering recipe of a contextual image.

    :param data_source: data source to get the image recipe from
    :param name: the name of the image in `workspace.json`
    :return: the registering recipe of the contextual image
    """

    path: str | None = get_contextual_image_recipe_path(data_source, name)
    if not path:
        return f"Could not find recipe for image {name} in source {data_source}", 404

    # Get the recipe points
    points: dict = load_points_dict(path)
    if not points:
        return f"Could not find registering points at {path}", 404

    return points, 200
