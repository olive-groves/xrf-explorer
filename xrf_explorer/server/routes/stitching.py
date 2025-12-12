import traceback

from flask import request, jsonify

from logging import Logger, getLogger

from xrf_explorer import app
from xrf_explorer.server.stitcher.stitcher_service import stitch_greyscales, generate_all_partial_greyscales, stitch, get_stitch_info, validate_stitching_data, StitchData

LOG: Logger = getLogger(__name__)

@app.route("/api/<data_source>/stitch_datacubes/get_stitch_info", methods=["POST"])
def get_stitching_info(data_source: str):
    """
    Provides the optimal scalar for stitching and a predicted file size for scaling predictions based on the provided JSON configuration.

    Args:
        data_source (str): Identifier for the data source.

    JSON Payload:
        type (str): Must be 'elemental' or 'spectral'.
        preview (bool): If true, only generate greyscale preview without full stitching.
        contextual_image (str): Path to contextual image for frame dimensions (or "base" for workspace base image).
        down_scaling (float): Scaling factor between 0 and 1.
        fragments (list[dict]): List of fragments containing:
            - datacube_file (str): Path to datacube file
            - rpl_file (str): Path to RPL file (spectral only, optional if preview=true)
            - rotation (int): Rotation in degrees (0, 90, 180, 270)
            - local_points (dict): Points in fragment coordinates
            - target_points (dict): Points in target frame coordinates
            Each points dict has: top_left, top_right, bottom_left, bottom_right as [x, y] arrays.

    Returns:
        JSON response with status and result information.
    """
    data = request.get_json()

    # Validate request
    is_valid, error_msg = validate_stitching_data(data)
    if not is_valid:
        return jsonify({"error": error_msg}), 400

    # Parse stitch data
    stitch_configuration = StitchData(data, data_source)

    try:
        result = get_stitch_info(stitch_configuration)
        return jsonify(result), 200
    except FileNotFoundError as e:
        LOG.error(e)
        return jsonify({"error": f"File not found: {str(e)}"}), 404
    except ValueError as e:
        LOG.error(e)
        return jsonify({"error": f"Validation error: {str(e)}"}), 400
    except Exception as e:
        LOG.error(e)
        return jsonify({"error": f"Stitching failed: {str(e)}"}), 500

@app.route(
    "/api/<data_source>/stitch_datacubes/generate_partial_greyscales", methods=["POST"]
)
def generate_partial_greyscales(data_source: str):
    """
    Stitches datacube fragments or greyscale images based on the provided JSON configuration.

    Args:
        data_source (str): Identifier for the data source.

    JSON Payload:
        type (str): Must be 'elemental' or 'spectral'.
        preview (bool): If true, only generate greyscale preview without full stitching.
        contextual_image (str): Path to contextual image for frame dimensions (or "base" for workspace base image).
        down_scaling (float): Scaling factor between 0 and 1.
        fragments (list[dict]): List of fragments containing:
            - datacube_file (str): Path to datacube file
            - rpl_file (str): Path to RPL file (spectral only, optional if preview=true)
            - rotation (int): Rotation in degrees (0, 90, 180, 270)
            - local_points (dict): Points in fragment coordinates
            - target_points (dict): Points in target frame coordinates
            Each points dict has: top_left, top_right, bottom_left, bottom_right as [x, y] arrays.

    Returns:
        JSON response with status and result information.
    """
    data = request.get_json()

    # Validate request
    is_valid, error_msg = validate_stitching_data(data)
    if not is_valid:
        return jsonify({"error": error_msg}), 400

    # Parse stitch data
    stitch_configuration = StitchData(data, data_source)

    try:
        result = generate_all_partial_greyscales(stitch_configuration)
        return jsonify(result), 200
    except FileNotFoundError as e:
        LOG.error(e)
        return jsonify({"error": f"File not found: {str(e)}"}), 404
    except ValueError as e:
        LOG.error(e)
        return jsonify({"error": f"Validation error: {str(e)}"}), 400
    except Exception as e:
        LOG.error(e)
        return jsonify({"error": f"Stitching failed: {str(e)}"}), 500



@app.route("/api/<data_source>/stitch_datacubes/stitch", methods=["POST"])
def stitching(data_source: str):
    """
    Stitches datacube fragments or greyscale images based on the provided JSON configuration.

    Args:
        data_source (str): Identifier for the data source.

    JSON Payload:
        type (str): Must be 'elemental' or 'spectral'.
        preview (bool): If true, only generate greyscale preview without full stitching.
        contextual_image (str): Path to contextual image for frame dimensions (or "base" for workspace base image).
        down_scaling (float): Scaling factor between 0 and 1.
        fragments (list[dict]): List of fragments containing:
            - datacube_file (str): Path to datacube file
            - rpl_file (str): Path to RPL file (spectral only, optional if preview=true)
            - rotation (int): Rotation in degrees (0, 90, 180, 270)
            - local_points (dict): Points in fragment coordinates
            - target_points (dict): Points in target frame coordinates
            Each points dict has: top_left, top_right, bottom_left, bottom_right as [x, y] arrays.

    Returns:
        JSON response with status and result information.
    """
    data = request.get_json()

    # Validate request
    is_valid, error_msg = validate_stitching_data(data)
    if not is_valid:
        return jsonify({"error": error_msg}), 400

    print(len(data["fragments"]))

    # Parse stitch data
    stitch_configuration = StitchData(data, data_source)

    print(len(stitch_configuration.points))

    try:
        result = stitch(stitch_configuration)
        return jsonify(result), 200
    except FileNotFoundError as e:
        LOG.error(traceback.format_exc())
        return jsonify({"error": f"File not found: {str(e)}"}), 404
    except ValueError as e:
        LOG.error(traceback.format_exc())
        return jsonify({"error": f"Validation error: {str(e)}"}), 400
    except Exception as e:
        LOG.error(traceback.format_exc())
        return jsonify({"error": f"Stitching failed: {str(e)}"}), 500
