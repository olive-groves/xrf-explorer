"""Contains API Routes relating to stitching and greyscale generation."""

import traceback
from os.path import abspath

from flask import request, jsonify, send_file

from logging import Logger, getLogger

from xrf_explorer import app
from xrf_explorer.server.stitcher import (
    generate_all_partial_greyscales,
    stitch,
    get_stitch_info,
    StitchData,
    pre_transpose_cubes,
    get_transpose_status,
    get_greyscale_path
)
from xrf_explorer.server.file_system.workspace import get_workspace_dict
from xrf_explorer.server.file_system.workspace.workspace_handler import update_workspace
from xrf_explorer.server.database.authnew import userCanAccessProject


LOG: Logger = getLogger(__name__)

@app.route("/api/<data_source>/stitch_datacubes/get_stitch_info", methods=["POST"])
@userCanAccessProject
def get_stitching_info(data_source: str):
    """
    Provides the optimal scalar for stitching and a predicted file size for scaling predictions based on the provided JSON configuration.

    Args:
        data_source (str): Identifier for the data source.

    JSON Payload:
        type (str): Must be 'elemental' or 'spectral'.
        contextual_image (str): Path to contextual image for frame dimensions (or "base" for workspace base image).
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

    # Parse request data
    try:
        stitch_configuration = StitchData(data, data_source)
    except (ValueError, KeyError) as e:
        LOG.error(e)
        return jsonify({"error": f"Error while parsing request data: {str(e)}"}), 400

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

@app.route("/api/<data_source>/stitch_datacubes/generate_partial_greyscales", methods=["POST"])
@userCanAccessProject
def generate_partial_greyscales(data_source: str):
    """
    Stitches datacube fragments or greyscale images based on the provided JSON configuration.

    Args:
        data_source (str): Identifier for the data source.

    JSON Payload:
        type (str): Must be 'elemental' or 'spectral'.
        fragments (list[dict]): List of fragments containing:
            - datacube_file (str): Path to datacube file
            - rpl_file (str): Path to RPL file (spectral only, optional if preview=true)

    Returns:
        JSON response with status and result information.
    """
    data = request.get_json()

    # Parse request data
    try:
        stitch_configuration = StitchData(data, data_source)
    except (ValueError, KeyError) as e:
        LOG.error(e)
        return jsonify({"error": f"Error while parsing request data: {str(e)}"}), 400

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

@app.route("/api/<data_source>/stitch_datacubes/greyscale_image/<fragment_name>", methods=["GET"])
@userCanAccessProject
def get_partial_greyscale(data_source: str, fragment_name: str):
    """
    Retrieves and serves a partial fragment greyscale image as a response. The image
    is located in the generated/stitching folder of the provided datasource.

    Args:
        data_source (str): Name of the data source the greyscale belongs to.
        fragment_name (str): Name of the fragment to get the greyscale image from.

    Returns:
        Response: A Flask response object containing the greyscale image
        file with the mimetype set as 'image/png'.
    """
    path = get_greyscale_path(fragment_name, data_source)
    return send_file(abspath(path), mimetype='image/png')

@app.route("/api/<data_source>/stitch_datacubes/stitched_greyscale/", methods=["GET"])
@userCanAccessProject
def get_stitched_greyscale(data_source: str):
    """
    Retrieves and serves a stitched greyscale preview image as a response. The image
    is located in the generated/stitching folder of the provided datasource.

    Args:
        data_source (str): Name of the data source the greyscale preview belongs to.

    Returns:
        Response: A Flask response object containing the greyscale image
        file with the mimetype set as 'image/png'.
    """
    path = get_greyscale_path("preview", data_source)
    return send_file(abspath(path), mimetype='image/png')


@app.route("/api/<data_source>/stitch_datacubes/stitch", methods=["POST"])
@userCanAccessProject
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

    # Parse request data
    try:
        stitch_configuration = StitchData(data, data_source, is_stitching=True)
    except (ValueError, KeyError) as e:
        LOG.error(e)
        return jsonify({"error": f"Error while parsing request data: {str(e)}"}), 400

    try:
        result = stitch(stitch_configuration)
        workspace = get_workspace_dict(data_source)
        if "stitchingMode" in workspace and workspace["stitchingMode"] == "partial":
            workspace["stitchingMode"] = "full"
        mapping = workspace.get("mapping")
        if isinstance(mapping, dict) and mapping.get("mode") == "preview":
            mapping["mode"] = "edit"
        update_workspace(data_source, workspace)
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


@app.route("/api/<data_source>/stitch_datacubes/pre_transpose_cubes", methods=["POST"])
@userCanAccessProject
def pre_transpose_cubes_endpoint(data_source: str):
    """
    Pre-transposes spectral datacubes in the background to speed up later stitching.

    This endpoint starts background transpose operations for all spectral datacubes
    specified in the request. The transpose operation converts cubes from (H, W, C)
    to (C, H, W) format which is required for efficient stitching.

    The endpoint returns immediately with status 202 Accepted. Use the
    transpose_status endpoint to check progress.

    Args:
        data_source (str): Identifier for the data source.

    JSON Payload:
        type (str): Must be 'spectral' (elemental cubes don't need transposing).
        fragments (list[dict]): List of fragments containing:
            - datacube_file (str): Path to datacube file
            - rpl_file (str): Path to RPL file
            
    Returns:
        JSON response with:
            - status: "started" if transpose operations were initiated
            - message: Description of what was started
            - cubes: List of cube files being transposed
    """
    data = request.get_json()

    # Parse request data
    try:
        stitch_configuration = StitchData(data, data_source)
    except (ValueError, KeyError) as e:
        LOG.error(e)
        return jsonify({"error": f"Error while parsing request data: {str(e)}"}), 400
    
    try:
        result = pre_transpose_cubes(stitch_configuration)
        return jsonify(result), 202  # 202 Accepted - processing started
    except FileNotFoundError as e:
        LOG.error(traceback.format_exc())
        return jsonify({"error": f"File not found: {str(e)}"}), 404
    except ValueError as e:
        LOG.error(traceback.format_exc())
        return jsonify({"error": f"Validation error: {str(e)}"}), 400
    except Exception as e:
        LOG.error(traceback.format_exc())
        return jsonify({"error": f"Pre-transpose failed: {str(e)}"}), 500


@app.route("/api/<data_source>/stitch_datacubes/transpose_status", methods=["GET"])
@userCanAccessProject
def transpose_status_endpoint(data_source: str):
    """
    Returns the current status of pre-transpose operations for a data source.
    
    This endpoint allows clients to check whether pre-transpose operations
    are still in progress, completed, or have not been started.
    
    Args:
        data_source (str): Identifier for the data source.
    
    Returns:
        JSON response with:
            - data_source: The data source name
            - any_in_progress: Boolean indicating if any transposes are running
            - cubes: Dictionary mapping cube filenames to their status objects
                Each status object contains:
                    - status: "not_started", "in_progress", "completed", or "failed"
                    - transposed_path: Path to transposed cube (if completed)
                    - error: Error message (if failed)
                    - started_at: Timestamp when transpose started
                    - completed_at: Timestamp when transpose completed
    """
    try:
        result = get_transpose_status(data_source)
        return jsonify(result), 200
    except Exception as e:
        LOG.error(traceback.format_exc())
        return jsonify({"error": f"Failed to get transpose status: {str(e)}"}), 500
