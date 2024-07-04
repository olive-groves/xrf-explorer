import logging

from os import rmdir, makedirs, remove
from os.path import join, exists, isdir, isfile
from shutil import rmtree

import pytest
import json

from flask.testing import FlaskClient
from werkzeug.test import TestResponse

import numpy as np

from xrf_explorer import app
from xrf_explorer.server.file_system.helper import set_config

RESOURCES_PATH: str = join("tests", "resources")


class TestRoutes:
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, "configs", "routes.yml")
    DATA_SOURCES_FOLDER: str = join(RESOURCES_PATH, "data_sources")

    DATA_SOURCE: str = "test_data_source"
    GENERATED_FOLDER: str = join(DATA_SOURCES_FOLDER, DATA_SOURCE, "generated")

    BASE_IMAGE: str = "BASE"
    CONTEXTUAL_IMAGE: str = "CONTEXTUAL"
    ELEMENT_NAMES: list[str] = ["yAl K", "Si K", "not an element"]
    ELEMENTAL_CUBE: np.ndarray = np.array(
        [[
            [1, 2, 3], 
            [4, 5, 6],
            [7, 8, 9]
        ], [
            [10, 20, 30], 
            [40, 50, 60],
            [70, 80, 90]
        ], [
            [100, 200, 300], 
            [400, 500, 600],
            [700, 800, 900]
        ]]
    )
    RECIPE: dict = {
        "moving":[[0.0,0.0],[0.0,1.0],[1.0,0.0],[1.0,1.0]],
        "target":[[0.0,0.0],[0.0,1.0],[1.0,0.0],[1.0,1.0]]
    }

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
        file: dict = client.get(f"/api/{self.DATA_SOURCE}/workspace").json

        # verify
        assert len(file) > 0
    
    def test_get_workspace_invalid_data_source(self, client: FlaskClient):
        # execute
        file: TestResponse = client.get("/api/this is not a data source/workspace")

        # verify
        assert file.status_code == 404

    def test_datasource_files(self, client: FlaskClient):
        # execute
        response: TestResponse = client.get(f"/api/{self.DATA_SOURCE}/files")

        # verify
        assert response.status_code == 200
    
    def test_create_data_source_dir(self, client: FlaskClient):
        # setup
        completely_new_data_source: str = "completely_new_data_source"
        folder_path: str = join(self.DATA_SOURCES_FOLDER, completely_new_data_source)

        # execute
        response: TestResponse = client.post(f"/api/{completely_new_data_source}/create")

        # verify
        assert response.status_code == 200
        assert response.json == {"dataSourceDir": completely_new_data_source}
        assert isdir(folder_path)

        # cleanup
        rmdir(folder_path)

    def test_create_data_source_dir_existing_name(self, client: FlaskClient):
        # execute
        response: TestResponse = client.post(f"/api/{self.DATA_SOURCE}/create")

        # verify
        assert response.status_code == 400
        assert response.text == "Data source name already exists."
    
    def test_create_data_source_dir_no_config(self, client: FlaskClient, caplog):
        # setup
        set_config("this is not a config file.yml")
        error_msg: str = "Error occurred while creating data source directory" 

        # execute
        response: TestResponse = client.post("/api/completely_new_data_source/create")

        # verify
        assert response.status_code == 500
        assert response.text == error_msg 
        assert error_msg in caplog.text
    
    def test_remove_data_source(self, client: FlaskClient):
        # setup
        completely_new_data_source: str = "completely_new_data_source"
        folder_path: str = join(self.DATA_SOURCES_FOLDER, completely_new_data_source)

        # setup - create data source with workspace and generated folder
        makedirs(folder_path)
        makedirs(join(folder_path, "generated"))
        with open(join(folder_path, "workspace.json"), "w") as f:
            f.write("{}")

        # execute
        response: TestResponse = client.post(f"/api/{completely_new_data_source}/remove")

        # verify
        assert response.status_code == 200
        assert response.get_json() == {"dataSourceDir": completely_new_data_source}
        assert not isdir(folder_path)
    
    def test_remove_data_source_no_config(self, client: FlaskClient, caplog):
        # setup
        set_config("this is not a config file.yml")
        error_msg: str = "Error occurred while removing data source directory"

        # execute
        response: TestResponse = client.post(f"/api/completely_new_data_source/remove")

        # verify
        assert response.status_code == 500
        assert response.text == error_msg 
        assert error_msg in caplog.text
    
    def test_upload_chunk(self, client: FlaskClient):
        # setup
        file_name: str = "test_file.txt"
        file_path: str = join(self.DATA_SOURCES_FOLDER, self.DATA_SOURCE, file_name)

        # execute
        response: TestResponse = client.post(
            f"/api/{self.DATA_SOURCE}/upload/{file_name}/0", data=b"This is a test chunk"
        )

        # verify
        assert response.status_code == 200
        assert response.text == "Uploaded file chunk"
        assert isfile(file_path)

        # cleanup
        remove(file_path)
    
    def test_upload_chunk_no_config(self, client: FlaskClient, caplog):
        # setup
        set_config("this is not a config file.yml")
        error_msg: str = "Error occurred while uploading file chunk"

        # execute
        response: TestResponse = client.post(
            f"/api/{self.DATA_SOURCE}/upload/a_new_file/0", data=b"This is a test chunk"
        )

        # verify
        assert response.status_code == 500
        assert response.text == error_msg 
        assert error_msg in caplog.text
    
    def test_convert_elemental_cube(self, client: FlaskClient):
        # execute
        response: TestResponse = client.get(f"/api/{self.DATA_SOURCE}/data/convert")

        # verify
        assert response.status_code == 200
        assert response.text == "Converted elemental data cube to .dms format"

    def test_convert_elemental_cube_invalid_data_source(self, client: FlaskClient):
        # execute
        response: TestResponse = client.get("/api/this is not a data source/data/convert")

        # verify
        assert response.status_code == 500
    
    def test_bin_raw_data_already_binned(self, client: FlaskClient):
        # execute
        response: TestResponse = client.post(f"/api/{self.DATA_SOURCE}/bin_raw/")

        # verify
        assert response.status_code == 200
        assert response.text == "Data already binned"

    def test_bin_raw_data_invalid_data_source(self, client: FlaskClient):
        # execute
        response: TestResponse = client.post("/api/this is not a data source/bin_raw/")

        # verify
        assert response.status_code == 500
    
    def test_get_offset(self, client: FlaskClient):
        # execute
        offset: str = client.get(f"/api/{self.DATA_SOURCE}/get_offset").text

        # verify
        assert float(offset) == -0.956
    
    def test_get_offset_invalid_data_source(self, client: FlaskClient):
        # execute
        offset: dict = client.get("/api/this is not a data source/get_offset").text

        # verify
        assert offset == "0"
    
    def test_list_element_averages(self, client: FlaskClient):
        # execute
        result: str = client.get(f"/api/{self.DATA_SOURCE}/element_averages").text

        # verify
        assert len(json.loads(result)) == 3
    
    def test_element_averages_selection_invalid_json(self, client: FlaskClient):
        # execute
        response: TestResponse = client.post(f"/api/{self.DATA_SOURCE}/element_averages_selection", json={
            "something": "invalid"
        })

        # verify
        assert response.status_code == 400
        assert response.text == "Error occurred while getting selection type or points from request body"
    
    def test_element_averages_selection_invalid_type(self, client: FlaskClient):
        # setup
        selection_type: str = "invalid_type"

        # execute
        response: TestResponse = client.post(f"/api/{self.DATA_SOURCE}/element_averages_selection", json={
            "type": selection_type,
            "points": [
                {"x": 0, "y": 0},
                {"x": 1, "y": 1}
            ]
        })

        # verify
        assert response.status_code == 400
        assert response.text == f"Error parsing selection of type {selection_type}"
    
    def test_element_averages_selection_invalid_points_type(self, client: FlaskClient):
        # execute
        response: TestResponse = client.post(f"/api/{self.DATA_SOURCE}/element_averages_selection", json={
            "type": "rectangle",
            "points": "not a list of points"
        })

        # verify
        assert response.status_code == 400
        assert response.text == "Error parsing points; expected a list of points"
    
    def test_element_averages_selection(self, client: FlaskClient):
        # execute
        response: str = client.post(f"/api/{self.DATA_SOURCE}/element_averages_selection", json={
            "type": "rectangle",
            "points": [
                {"x": 0, "y": 0},
                {"x": 1, "y": 1}
            ]
        }).text

        # verify
        assert len(json.loads(response)) == 3
    
    def test_list_element_names(self, client: FlaskClient):
        # execute
        result_str: str = client.get(f"/api/{self.DATA_SOURCE}/data/elements/names").text
        print(result_str)
        result_list: list[str] = json.loads(result_str)

        # verify
        assert result_list == self.ELEMENT_NAMES
    
    def test_contextual_image(self, client: FlaskClient):
        # execute
        response: TestResponse = client.get(f"/api/{self.DATA_SOURCE}/image/{self.BASE_IMAGE}")

        # verify
        assert response.status_code == 200
        assert response.data
    
    def test_contextual_image_invalid_image(self, client: FlaskClient):
        # setup
        name: str = "not an image"

        # execute
        response: TestResponse = client.get(f"/api/{self.DATA_SOURCE}/image/{name}")

        # verify
        assert response.status_code == 404
        assert response.text == f"Image {name} not found in source {self.DATA_SOURCE}"
    
    def test_contextual_image_size(self, client: FlaskClient):
        # execute
        response: TestResponse = client.get(f"/api/{self.DATA_SOURCE}/image/{self.BASE_IMAGE}/size")

        # verify
        assert response.status_code == 200
        assert response.json == {"width": 3, "height": 3}
    
    def test_contextual_image_size_invalid_image(self, client: FlaskClient):
        # setup
        name: str = "not an image"

        # execute
        response: TestResponse = client.get(f"/api/{self.DATA_SOURCE}/image/{name}/size")

        # verify
        assert response.status_code == 404
        assert response.text == f"Image {name} not found in source {self.DATA_SOURCE}"
    
    def test_contextual_image_recipe(self, client: FlaskClient):
        # execute
        response: TestResponse = client.get(f"/api/{self.DATA_SOURCE}/image/{self.CONTEXTUAL_IMAGE}/recipe")

        # verify
        assert response.status_code == 200
        assert response.json == self.RECIPE
    
    def test_contextual_image_recipe_invalid_name(self, client: FlaskClient):
        # setup
        name: str = "not an image"

        # execute
        response: TestResponse = client.get(f"/api/{self.DATA_SOURCE}/image/{name}/recipe")

        # verify
        assert response.status_code == 404
        assert response.text == f"Could not find recipe for image {name} in source {self.DATA_SOURCE}"

    def test_data_cube_size(self, client: FlaskClient):
        # execute
        response: TestResponse = client.get(f"/api/{self.DATA_SOURCE}/data/size")

        # verify
        assert response.status_code == 200
        assert response.json == {"width": 3, "height": 3}

    def test_data_cube_recipe(self, client: FlaskClient):
        # execute
        recipe: dict = client.get(f"/api/{self.DATA_SOURCE}/data/recipe").json

        # verify
        assert len(recipe) > 0

    def test_data_cube_recipe_invalid_data_source(self, client: FlaskClient):
        # execute
        recipe: TestResponse = client.get("/api/this is not a data source/data/recipe")

        # verify
        assert recipe.status_code == 404
    
    def test_elemental_map(self, client: FlaskClient):
        # execute
        response: TestResponse = client.get(f"/api/{self.DATA_SOURCE}/data/elements/map/0")

        # verify
        assert response.status_code == 200
        assert response.data
    
    def test_elemental_map_invalid_data_source(self, client: FlaskClient):
        # setup
        data_source: str = "not a data source"

        # execute
        response: TestResponse = client.get(f"/api/{data_source}/data/elements/map/0")

        # verify
        assert response.status_code == 404
        assert response.text == f"Could not find elemental data cube in source {data_source}"

    def test_get_selection_spectra_invalid_selection_type(self, client: FlaskClient):
        selection: dict = {
            "type": "invalid_type",
            "points": [
                {"x": 0, "y": 0},
                {"x": 1, "y": 1}
            ]
        }

        # execute
        response: TestResponse = client.post(f"/api/{self.DATA_SOURCE}/get_selection_spectrum", json=selection)

        # verify
        assert response.status_code == 400
        assert response.get_data(as_text=True) == "Error parsing selection type"

    def test_get_color_clusters_whole_cube(self, client: FlaskClient):
        # execute
        response: TestResponse = client.get(f"/api/{self.DATA_SOURCE}/cs/clusters/0/1/100")

        # verify
        assert response.status_code == 200
        assert response.text

        # cleanup
        rmtree(self.GENERATED_FOLDER)
    
    def test_get_color_clusters_single_element(self, client: FlaskClient):
        # execute
        response: TestResponse = client.get(f"/api/{self.DATA_SOURCE}/cs/clusters/1/1/0")

        # verify
        assert response.status_code == 200
        assert response.text

        # cleanup
        rmtree(self.GENERATED_FOLDER)
    
    def test_get_color_clusters_already_present(self, client: FlaskClient):
        # setup
        url: str = f"/api/{self.DATA_SOURCE}/cs/clusters/1/1/0"

        # execute
        response1: TestResponse = client.get(url)
        response2: TestResponse = client.get(url)

        # verify
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.text == response2.text

        # cleanup
        rmtree(self.GENERATED_FOLDER)
    
    def test_get_color_cluster_bitmask_whole_cube(self, client: FlaskClient):
        # execute
        response: TestResponse = client.get(f"/api/{self.DATA_SOURCE}/cs/bitmask/0/1/100")

        # verify
        assert response.status_code == 200
        assert response.data

        # cleanup
        response.close()
        rmtree(self.GENERATED_FOLDER)
    
    def test_get_color_cluster_bitmask_single_element(self, client: FlaskClient):
        # execute
        response: TestResponse = client.get(f"/api/{self.DATA_SOURCE}/cs/bitmask/1/1/0")

        # verify
        assert response.status_code == 200
        assert response.data

        # cleanup
        response.close()
        rmtree(self.GENERATED_FOLDER)
    
    def test_get_color_cluster_bitmask_no_config(self, client: FlaskClient):
        # setup
        set_config("this is not a config file.yml")

        # execute
        response: TestResponse = client.get(f"/api/{self.DATA_SOURCE}/cs/bitmask/1/1/0")

        # verify
        assert response.status_code == 500
        assert response.text == 'Error occurred while getting backend config'
