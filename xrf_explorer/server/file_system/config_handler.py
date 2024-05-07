import logging

import yaml

LOG: logging.Logger = logging.getLogger(__name__)


def load_yml(path: str) -> dict:
    with open(path, 'r') as config_file:
        try:
            return yaml.safe_load(config_file)
        except yaml.YAMLError:
            LOG.exception("Failed to access config at {%s}", path)
            return {}
