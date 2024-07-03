import logging

from os import rmdir, makedirs, remove
from os.path import join, exists, isdir, isfile
import pytest
import json

from flask import Response
from flask.testing import FlaskClient

from xrf_explorer import app
from xrf_explorer.server.file_system.helper import set_config

RESOURCES_PATH: str = join("tests", "resources")

class TestRoutes:
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, "configs", "routes.yml")
    DATA_SOURCES_FOLDER: str = join(RESOURCES_PATH, "data_sources")

    DATA_SOURCE: str = "test_data_source"

    @pytest.fixture()
    def client(self):
        return app.test_client()

    @pytest.fixture(autouse=True)
    def setup_environment(self):
        set_config(self.CUSTOM_CONFIG_PATH)
        yield

    def test_api(self, client: FlaskClient):
        # execute
        apis: str = client.get("/api").json

        # verify
        assert len(apis) >= 10
    
    def test_get_datasources(self, client: FlaskClient):
        # execute
        result_str: str = client.get("/api/datasources").text
        result_list: list[str] = json.loads(result_str)

        # verify
        assert len(result_list) == 1
    
    def test_get_workspace(self, client: FlaskClient):
        # execute
        file = client.get(f"/api/{self.DATA_SOURCE}/workspace").json

        # verify
        assert len(file) > 0
    
    def test_get_workspace_invalid_data_source(self, client: FlaskClient):
        # execute
        file = client.get("/api/this is not a data source/workspace")

        # verify
        assert file.status_code == 404
    
    def test_data_cube_recipe(self, client: FlaskClient):
        # execute
        recipe: dict = client.get(f"/api/{self.DATA_SOURCE}/data/recipe").json

        # verify
        assert len(recipe) > 0

    def test_data_cube_recipe_invalid_data_source(self, client: FlaskClient):
        # execute
        recipe = client.get("/api/this is not a data source/data/recipe")

        # verify
        assert recipe.status_code == 404

    def test_convert_elemental_cube(self, client: FlaskClient):
        # execute
        response = client.get(f"/api/{self.DATA_SOURCE}/data/convert")

        # verify
        assert response.status_code == 200
        assert response.text == "Converted elemental data cube to .dms format"

    def test_convert_elemental_cube_invalid_data_source(self, client: FlaskClient):
        # execute
        response = client.get("/api/this is not a data source/data/convert")

        # verify
        assert response.status_code == 500

    def test_bin_raw_data_already_binned(self, client: FlaskClient):
        # execute
        response = client.post(f"/api/{self.DATA_SOURCE}/bin_raw/")

        # verify
        assert response.status_code == 200
        assert response.text == "Data already binned"

    def test_bin_raw_data_invalid_data_source(self, client: FlaskClient):
        # execute
        response = client.post("/api/this is not a data source/bin_raw/")

        # verify
        assert response.status_code == 500

    def test_list_element_names(self, client: FlaskClient):
        # execute
        result_str: str = client.get(f"/api/{self.DATA_SOURCE}/data/elements/names").text
        result_list: list[str] = json.loads(result_str)

        # verify
        assert len(result_list) >= 0

    def test_datasource_files(self, client: FlaskClient):
        # execute
        response = client.get(f"/api/{self.DATA_SOURCE}/files")

        # verify
        assert response.status_code == 200

    def test_create_data_source_dir(self, client: FlaskClient):
        # setup
        completely_new_data_source = "completely_new_data_source"
        folder_path: str = join(self.DATA_SOURCES_FOLDER, completely_new_data_source)

        # execute
        response = client.post(f"/api/{completely_new_data_source}/create")

        # verify
        assert response.status_code == 200
        assert response.json == {"dataSourceDir": completely_new_data_source}
        assert isdir(folder_path)

        # cleanup
        rmdir(folder_path)

    def test_create_data_source_dir_existing_name(self, client: FlaskClient):
        # execute
        response = client.post(f"/api/{self.DATA_SOURCE}/create")

        # verify
        assert response.status_code == 400
        assert response.text == "Data source name already exists."

    def test_remove_data_source(self, client: FlaskClient):
        # setup
        completely_new_data_source = "completely_new_data_source"
        folder_path: str = join(self.DATA_SOURCES_FOLDER, completely_new_data_source)

        # setup - create data source with workspace and generated folder
        makedirs(folder_path)
        makedirs(join(folder_path, "generated"))
        with open(join(folder_path, "workspace.json"), "w") as f:
            f.write("{}")

        # execute
        response = client.post(f"/api/{completely_new_data_source}/remove")

        # verify
        assert response.status_code == 200
        assert response.get_json() == {"dataSourceDir": completely_new_data_source}
        assert not isdir(folder_path)

    def test_upload_chunk(self, client: FlaskClient):
        # setup
        file_name: str = "test_file.txt"
        file_path: str = join(self.DATA_SOURCES_FOLDER, self.DATA_SOURCE, file_name)

        # execute
        response = client.post(f"/api/{self.DATA_SOURCE}/upload/{file_name}/0", data=b"This is a test chunk")

        # verify
        assert response.status_code == 200
        assert response.text == "Uploaded file chunk"
        assert isfile(file_path)

        # cleanup
        remove(file_path)

    def test_get_selection_spectra_invalid_selection_type(self, client: FlaskClient):
        selection = {
            "type": "invalid_type",
            "points": [
                {"x": 0, "y": 0},
                {"x": 1, "y": 1}
            ]
        }

        # execute
        response = client.post(f"/api/{self.DATA_SOURCE}/get_selection_spectrum", json=selection)

        # verify
        assert response.status_code == 400
        assert response.get_data(as_text=True) == "Error parsing selection type"
