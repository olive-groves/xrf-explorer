from logging import Logger, getLogger
from os.path import abspath

from flask import request, send_file

from xrf_explorer import app

from xrf_explorer.server.dim_reduction import (
    generate_embedding,
    create_embedding_image,
    get_image_of_indices_to_embedding
)

LOG: Logger = getLogger(__name__)


@app.route("/api/<data_source>/dr/embedding/<int:element>/<int:threshold>")
def get_dr_embedding(data_source: str, element: int, threshold: int):
    """
    Generate the dimensionality reduction embedding of an element, given a threshold.

    :param data_source: data source to generate the embedding from
    :param element: element to generate the embedding for
    :param threshold: threshold from which a pixel is selected
    :return: string code indicating the status of the embedding generation.
             "success" when embedding was generated successfully,
             "downsampled" when successful and the number of data points was down sampled.
    """
    scaled_threshold: int = int(255 * threshold / 100)
    # Try to generate the embedding
    result = generate_embedding(data_source, element, scaled_threshold, request.args)
    if result == "success" or result == "downsampled":
        return result

    error_msg: str = "Failed to create DR embedding image"
    LOG.error(error_msg)
    return error_msg, 400


@app.route("/api/<data_source>/dr/overlay/<overlay_type>")
def get_dr_overlay(data_source: str, overlay_type: str):
    """
    Generate the dimensionality reduction overlay with a given type.

    :param data_source: data source to get the overlay from
    :param overlay_type: the overlay type. Images are prefixed with contextual_ and elements by elemental_
    :return: overlay image file
    """

    # Try to get the embedding image
    image_path: str = create_embedding_image(data_source, overlay_type)
    if not image_path:
        error_msg: str = "Failed to create DR embedding image"
        LOG.error(error_msg)
        return error_msg, 400

    return send_file(abspath(image_path), mimetype='image/png')


@app.route("/api/<data_source>/dr/embedding/mapping")
def get_dr_embedding_mapping(data_source: str):
    """
    Creates the image for polygon selection that decodes to which points in the embedding the pixels of the elemental
    data cube are mapped. Uses the current embedding and indices for the given data source to create the image.

    :param data_source: data source to get the overlay from
    :return: image that decodes to which points in the embedding the pixels of the elemental data cube are mapped
    """

    # Try to get the image
    image_path: str = get_image_of_indices_to_embedding(data_source)
    if not image_path:
        error_msg: str = "Failed to create DR indices to embedding image"
        LOG.error(error_msg)
        return error_msg, 400

    return send_file(abspath(image_path), mimetype='image/png')
