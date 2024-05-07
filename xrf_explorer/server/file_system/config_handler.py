import logging

import yaml

LOG: logging.Logger = logging.getLogger(__name__)


def load_yml(path: str) -> dict:
    try:
        with open(path, 'r') as config_file:
            return yaml.safe_load(config_file)
    except (FileNotFoundError, yaml.YAMLError):
        LOG.exception("Failed to access config at {%s}", path)
        return {}
