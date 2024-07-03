import logging

from os.path import join
import pytest
import json

from xrf_explorer.server.file_system.helper import set_config
from xrf_explorer.server.routes import (
    list_accessible_data_sources
)

RESOURCES_PATH: str = join("tests", "resources")

class TestRoutes:
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, "configs", "routes.yml")

    @pytest.fixture(autouse=True)
    def setup_environment(self):
        set_config(self.CUSTOM_CONFIG_PATH)
        yield

    def test_get_average_global(self):
        # execute
        result_str: str = list_accessible_data_sources()
        result_list: list[str] = json.loads(result_str)

        # verify
        assert len(result_list) == 1
