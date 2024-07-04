from logging import Logger, getLogger

import numpy as np

from xrf_explorer.server.image_to_cube_selection import SelectionType, get_selection, CubeType

LOG: Logger = getLogger(__name__)


def validate_config(config: dict | None) -> tuple[str, int] | None:
    """
    Checks that the configuration has a valid format.

    :param config: the configuration to verify
    :return: None if the configuration is valid, otherwise a tuple with an error message and the HTTP response status
        code
    """
    if not config:
        error_msg: str = "Error occurred while getting backend config"
        LOG.error(error_msg)
        return error_msg, 500
    return None


def parse_selection(selection_data: dict[str: str]) -> tuple[SelectionType, list[tuple[int, int]]] | tuple[str, int]:
    """
    Parses a selection in JSON format and extracts the information therein.

    :param selection_data: the selection data in JSON format
    :return: The selection type and points or an error message and the HTTP response status code if an error occurred
    """
    # get selection type and points
    selection_type: str | None = selection_data.get('type')
    points: list[dict[str, float]] | None = selection_data.get('points')
    if selection_type is None or points is None:
        return "Error occurred while getting selection type or points from request body", 400

    # validate and parse selection type
    try:
        selection_type_parsed: SelectionType = SelectionType(selection_type)
    except ValueError:
        return f"Error parsing selection of type {selection_type}", 400

    # validate and parse points
    if not isinstance(points, list):
        return f"Error parsing points: expected a list of points, got {type(points)}", 400
    try:
        points_parsed: list[tuple[int, int]] = [(round(point['x']), round(point['y'])) for point in points]
    except ValueError:
        return "Error parsing points", 400

    return selection_type_parsed, points_parsed


def encode_selection(selection_data: any, data_source: str, cube_type: CubeType) -> np.ndarray | tuple[str, int]:
    """
    Creates a bitmask of the given cube from a selection in JSON format.

    :param selection_data: the selection data in JSON format as extracted from a request
    :param data_source: the name of the data source containing the cube
    :param cube_type: the type of the cube on which to apply the selection
    :return: bitmask of the cube encoding the selection or None if an error occurred
    """
    # parse JSON payload
    selection: SelectionType | str
    points: list[tuple[int, int]] | int
    selection, points = parse_selection(selection_data)

    if isinstance(points, int):
        return selection, points

    # get selection
    return get_selection(data_source, points, selection, cube_type)
