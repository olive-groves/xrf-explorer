import logging

from os.path import join
import pytest
import json

from flask.testing import FlaskClient

from xrf_explorer import app
from xrf_explorer.server.file_system.helper import set_config

RESOURCES_PATH: str = join("tests", "resources")

class TestRoutes:
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, "configs", "routes.yml")

    DATA_SOURCE: str = "test_data_source"

    @pytest.fixture()
    def client(self):
        return app.test_client()

    @pytest.fixture(autouse=True)
    def setup_environment(self):
        set_config(self.CUSTOM_CONFIG_PATH)
        yield

    def test_get_datasources(self, client: FlaskClient):
        # execute
        result_str: str = client.get("/api/datasources").text
        result_list: list[str] = json.loads(result_str)

        # verify
        assert len(result_list) == 1
