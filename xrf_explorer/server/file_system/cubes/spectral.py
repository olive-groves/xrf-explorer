from logging import Logger, getLogger

from xrf_explorer.server.file_system.workspace.file_access import get_workspace_dict

LOG: Logger = getLogger(__name__)


def parse_rpl(path: str) -> dict:
    """Parse the rpl file of a data source as a dictionary, containing the following info:
        - width
        - height
        - depth
        - offset
        - data length
        - data type
        - byte order
        - record by

    :param path: path to the rpl file
    :return: Dictionary containing the attributes' name and value
    """

    try:
        with open(path, "r") as in_file:
            # first split on linebreak
            info: list[str] = in_file.read().splitlines()
    except OSError as err:
        LOG.error("error while reading rpl file: {%s}", err)
        return {}

    parsed_rpl: dict[str, str] = {}
    if info:
        for line in info:
            split: list[str] = line.split()  # split on whitespace
            if len(split) == 2:
                # add tuple to dictionary
                parsed_rpl[split[0].strip()] = split[1].strip()
    else:
        LOG.error("Error while parsing rpl file: file empty")

    return parsed_rpl


def get_spectra_params(data_source: str) -> dict[str, int]:
    """
    Returns the spectrum parameters (low/high boundaries and bin size) of a data source.

    :param data_source: Name of the data source.
    :return: dictionary with the low, high and bin size values
    """
    workspace_dict: dict | None = get_workspace_dict(data_source)
    if workspace_dict is None:
        raise FileNotFoundError

    return workspace_dict["spectralParams"]
