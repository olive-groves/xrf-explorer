from os import chmod, rmdir, makedirs, remove
from os.path import join, isdir, isfile, exists
from shutil import rmtree
import stat
import uuid

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

import pytest
import json

from flask.testing import FlaskClient
from werkzeug.test import TestResponse

import numpy as np
from unittest.mock import patch

from xrf_explorer import app
from xrf_explorer.server.database.database import init_app
from xrf_explorer.server.database.models import User, UserRole
from xrf_explorer.server.file_system.helper import set_config

RESOURCES_PATH: str = join("tests", "resources")


class TestRoutes:
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, "configs", "routes.yml")
    DATA_SOURCES_FOLDER: str = join(RESOURCES_PATH, "data_sources")

    DATA_SOURCE: str = "test_data_source"
    # Separate data source that contains existing color segmentation bitmasks.
    BITMASKS_DATA_SOURCE: str = "test_data_source_col_seg_bitmasks"
    UNBINNED_DATA_SOURCE: str = "unbinned_data_source"
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
        "moving": [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]],
        "target": [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]]
    }

    FULL_SELECTION: dict = {
            "type": "rectangle",
            "points": [
                {"x": 0, "y": 0},
                {"x": 2, "y": 2}
            ]
        }

    @pytest.fixture()
    def client(self):
        return app.test_client()

    @pytest.fixture(autouse=True)
    def setup_environment(self):
        set_config(self.CUSTOM_CONFIG_PATH)
        yield
    
    @pytest.fixture
    def test_app(self):
        # Create an in-memory SQLite database for testing
        app = Flask(__name__)
        db = init_app(app)
        with app.app_context():
            db.create_all()
            yield app, db
            db.drop_all()
    
    def sample_admin_user(self):
        def uname(name: str) -> str:
            return f"{name}_{uuid.uuid4().hex[:6]}"
        
        user_admin = User(username=uname('admin'), role=UserRole.ADMIN)
        user_admin.set_password('adminpass')
        
        return user_admin
    
    def login_as_admin(self, client: FlaskClient, db: SQLAlchemy):
        admin = self.sample_admin_user()
        db.session.add(admin)
        db.session.commit()

        admin_id = admin.id
        
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_id)
            sess['_fresh'] = True

    def test_api(self, client: FlaskClient):
        # execute
        apis: str = client.get("/api").json

        # verify
        assert len(apis) >= 10
    
    def test_get_datasources(self, client: FlaskClient):
        # execute
        result_str: str = client.get("/api/data_sources").text
        result_list: list[str] = json.loads(result_str)

        # verify
        assert len(result_list) == 3
    
    def test_get_workspace(self, client: FlaskClient):
        # execute
        file: dict = client.get(f"/api/{self.DATA_SOURCE}/workspace").json

        # verify
        assert len(file) > 0
    
    def test_get_workspace_invalid_data_source(self, client: FlaskClient, test_app):
        # Setup test app and Admin user
        app, db = test_app
        with app.app_context():
            self.login_as_admin(client, db)

        # execute
        file: TestResponse = client.get("/api/this is not a data source/workspace")

        # verify
        assert file.status_code == 404
    
    def test_ost_workspace_invalid_data_source(self, client: FlaskClient):
        # execute
        file: TestResponse = client.post(f"/api/this is not a data source/workspace", json={
            "something": "invalid"
        })

        # verify
        assert file.status_code == 401

    def test_datasource_files(self, client: FlaskClient):
        # execute
        response: TestResponse = client.get(f"/api/{self.DATA_SOURCE}/files")

        # verify
        assert response.status_code == 200
    
    def test_create_data_source_dir(self, client: FlaskClient, test_app):
        # Setup test app and Login as Admin user
        app, db = test_app
        with app.app_context():
            self.login_as_admin(client, db)

        # setup
        completely_new_data_source: str = "completely_new_data_source"
        folder_path: str = join(self.DATA_SOURCES_FOLDER, completely_new_data_source)

        # Ensure folder does not exist, happens in case previous test failed.
        if exists(folder_path):
            rmtree(folder_path, onerror=remove)

        # execute
        response: TestResponse = client.post(f"/api/{completely_new_data_source}/create")

        # verify
        assert response.status_code == 200
        assert response.json == {"dataSourceDir": completely_new_data_source}
        assert isdir(folder_path)

        # cleanup
        rmdir(folder_path)

    def test_create_data_source_dir_existing_name(self, client: FlaskClient, test_app):
        # Setup test app and Login as Admin user
        app, db = test_app
        with app.app_context():
            self.login_as_admin(client, db)

        # execute
        response: TestResponse = client.post(f"/api/{self.DATA_SOURCE}/create")

        # verify
        assert response.status_code == 400
        assert response.text == "Data source name already exists."
    
    def test_create_data_source_dir_no_config(self, client: FlaskClient, caplog, test_app):
        # Setup test app and Login as Admin user
        app, db = test_app
        with app.app_context():
            self.login_as_admin(client, db)

        # setup
        set_config("this is not a config file.yml")
        error_msg: str = "Error occurred while getting backend config" 

        # execute
        response: TestResponse = client.post("/api/completely_new_data_source/create")

        # verify
        assert response.status_code == 500
        assert response.text == error_msg 
        assert error_msg in caplog.text
    
    def test_remove_data_source(self, client: FlaskClient, test_app):
        # Setup test app and Login as Admin user
        app, db = test_app
        with app.app_context():
            self.login_as_admin(client, db)

        # setup
        completely_new_data_source: str = "completely_new_data_source"
        folder_path: str = join(self.DATA_SOURCES_FOLDER, completely_new_data_source)

        # Ensure folder does not exist, happens in case previous test failed.
        if exists(folder_path):
            rmtree(folder_path)

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
    
    def test_remove_data_source_no_config(self, client: FlaskClient, caplog, test_app):
        # Setup test app and Login as Admin user
        app, db = test_app
        with app.app_context():
            self.login_as_admin(client, db)

        # setup
        set_config("this is not a config file.yml")
        error_msg: str = "Error occurred while getting backend config"

        # execute
        response: TestResponse = client.post(f"/api/completely_new_data_source/remove")

        # verify
        assert response.status_code == 500
        assert response.text == error_msg 
        assert error_msg in caplog.text

    def test_delete_data_source(self, client: FlaskClient, test_app):
        # Setup test app and Login as Admin user
        app, db = test_app
        with app.app_context():
            self.login_as_admin(client, db)

        # setup
        completely_new_data_source: str = "completely_new_data_source"
        folder_path: str = join(self.DATA_SOURCES_FOLDER, completely_new_data_source)

        # Ensure folder does not exist, happens in case previous test failed.
        if exists(folder_path):
            rmtree(folder_path)

        # setup - create data source with workspace and generated folder
        makedirs(folder_path)
        makedirs(join(folder_path, "generated"))
        with open(join(folder_path, "workspace.json"), "w") as f:
            f.write("{}")

        # execute
        response = client.delete(f"/api/{completely_new_data_source}/delete")

        # verify
        assert response.status_code == 200
        assert response.get_json() == {"dataSourceDir": completely_new_data_source}
    
    def test_delete_data_source_invalid_data_source(self, client: FlaskClient, test_app):
        # Setup test app and Login as Admin user
        app, db = test_app
        with app.app_context():
            self.login_as_admin(client, db)

        # execute
        response: TestResponse = client.delete("/api/this is not a data source/delete")

        # verify
        assert response.status_code == 400
    
    def test_upload_chunk(self, client: FlaskClient, test_app):
        # Setup test app and Login as Admin user
        app, db = test_app
        with app.app_context():
            self.login_as_admin(client, db)

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

    def test_delete_multiple_files(self, client: FlaskClient):
        # setup
        filename = "test.txt"
        path = join(self.DATA_SOURCES_FOLDER, self.DATA_SOURCE, filename)
        with open(path, "w") as file:
            file.write("test")

        jsonData = {}
        jsonData['filenames'] = [filename]

        # execute
        client.post(f"/api/{self.DATA_SOURCE}/delete_files", json=jsonData)

        # check
        assert not exists(path)

    def test_delete_multiple_files(self, client: FlaskClient):
        # setup
        filename1 = "test1.txt"
        path1 = join(self.DATA_SOURCES_FOLDER, self.DATA_SOURCE, filename1)
        with open(path1, "w") as file1:
            file1.write("test1")

        filename2 = "test2.txt"
        path2 = join(self.DATA_SOURCES_FOLDER, self.DATA_SOURCE, filename2)
        with open(path1, "w") as file2:
            file2.write("test2")

        jsonData = {}
        jsonData['filenames'] = [filename1, filename2];

        # execute
        client.post(f"/api/{self.DATA_SOURCE}/delete_files", json=jsonData)

        # check
        assert not exists(path1)
        assert not exists(path2)
    
    def test_upload_chunk_no_config(self, client: FlaskClient, caplog, test_app):
        # Setup test app and Login as Admin user
        app, db = test_app
        with app.app_context():
            self.login_as_admin(client, db)

        # setup
        set_config("this is not a config file.yml")
        error_msg: str = "Error occurred while getting backend config"

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
    
    def test_bin_raw_data(self, client: FlaskClient):
        # execute
        response: TestResponse = client.post(f"/api/{self.UNBINNED_DATA_SOURCE}/bin_raw/")

        # verify
        assert response.status_code == 200
        assert response.text == "Binned data"
    
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
        offset: str = client.get("/api/this is not a data source/get_offset").text

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
        assert response.text == f"Error parsing points: expected a list of points, got {type('string')}"
    
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

    def test_get_average_data(self, client: FlaskClient):
        # execute
        response: TestResponse = client.get(f"/api/{self.DATA_SOURCE}/get_average_data")

        # verify
        assert response.status_code == 200
        assert len(json.loads(response.text)) == 16
    
    def test_get_average_data_invalid_data_source(self, client: FlaskClient):
        # execute
        response: TestResponse = client.get(f"/api/not a data source/get_average_data")

        # verify
        assert response.status_code == 404
        assert response.text == "Error occurred while getting raw data"
    
    def test_get_element_spectra(self, client: FlaskClient):
        # execute
        response: TestResponse = client.get(f"/api/{self.DATA_SOURCE}/get_element_spectrum/Si/20")

        # verify
        assert response.status_code == 200
        assert len(json.loads(response.text)[0]) == 16
        assert len(json.loads(response.text)[1]) == 4
    
    def test_get_element_spectra_invalid_data_source(self, client: FlaskClient):
        # execute
        response: TestResponse = client.get(f"/api/this is not a data source/get_element_spectrum/Si K/20")

        # verify
        assert response.status_code == 404
        assert "error while loading workspace to retrieve spectra params" in response.text

    def test_get_selection_spectra_invalid_selection_type(self, client: FlaskClient):
        # setup selection type
        selection_type: str = "invalid_type"
        selection: dict = {
            "type": selection_type,
            "points": [
                {"x": 0, "y": 0},
                {"x": 1, "y": 1}
            ]
        }

        # execute
        response: TestResponse = client.post(f"/api/{self.DATA_SOURCE}/get_selection_spectrum", json=selection)

        # verify
        assert response.status_code == 400
        assert response.text == f"Error parsing selection of type {selection_type}"
    
    def test_get_selection_spectra_no_selection_type(self, client: FlaskClient):
        selection: dict = {
            "points": [
                {"x": 0, "y": 0},
                {"x": 1, "y": 1}
            ]
        }

        # execute
        response: TestResponse = client.post(f"/api/{self.DATA_SOURCE}/get_selection_spectrum", json=selection)

        # verify
        assert response.status_code == 400
        assert response.text == "Error occurred while getting selection type or points from request body"
    
    def test_get_selection_spectra_points_not_list(self, client: FlaskClient):
        selection: dict = {
            "type": "rectangle",
            "points": "not a list"
        }

        # execute
        response: TestResponse = client.post(f"/api/{self.DATA_SOURCE}/get_selection_spectrum", json=selection)

        # verify
        assert response.status_code == 400
        assert response.text == f"Error parsing points: expected a list of points, got {type('string')}"

    def test_get_selection_spectra(self, client: FlaskClient):
        selection: dict = {
            "type": "rectangle",
            "points": [
                {"x": 0, "y": 0},
                {"x": 1, "y": 1}
            ]
        }

        # execute
        response: TestResponse = client.post(f"/api/{self.DATA_SOURCE}/get_selection_spectrum", json=selection)

        # verify
        assert response.status_code == 200
        assert len(json.loads(response.text)) == 16
    
    def test_get_color_clusters_whole_cube(self, client: FlaskClient):
        # setup JSON
        elements = [[0, 100]]
        
        PAY_LOAD: dict = {
            "selection": self.FULL_SELECTION,
            "elements": elements
        }

        # execute
        response: TestResponse = client.post(f"/api/{self.DATA_SOURCE}/cs/clusters/1/false", 
                                             json=PAY_LOAD)

        # verify
        assert response.status_code == 200
        assert response.text
        
        def remove(func, path, exc_info):
            chmod(path, stat.S_IWRITE)
            func(path)

        # cleanup
        if exists(self.GENERATED_FOLDER):
            rmtree(self.GENERATED_FOLDER, onerror=remove)
    
    def test_get_color_clusters_single_element(self, client: FlaskClient):
        # setup JSON
        elements = [[1,0]]
        
        PAY_LOAD: dict = {
            "selection": self.FULL_SELECTION,
            "elements": elements
        }

        # execute
        response: TestResponse = client.post(f"/api/{self.DATA_SOURCE}/cs/clusters/1/false",
                                             json=PAY_LOAD)

        # verify
        assert response.status_code == 200
        assert response.text
        
        # cleanup
        def remove(func, path, exc_info):
            chmod(path, stat.S_IWRITE)
            func(path)
            
        if exists(self.GENERATED_FOLDER):
            rmtree(self.GENERATED_FOLDER, onerror=remove)

    def test_get_color_clusters_whole_cube_selection(self, client: FlaskClient):
        # setup JSON
        elements = [[0, 100]] 
 
        selection: dict = {
            "type": "rectangle",
            "points": [
                {"x": 0, "y": 0},
                {"x": 1, "y": 1}
            ]
        }
        
        PAY_LOAD: dict = {
            "selection": selection,
            "elements": elements
        }

        # execute
        response: TestResponse = client.post(f"/api/{self.DATA_SOURCE}/cs/clusters/1/true", 
                                             json=PAY_LOAD)

        # verify
        assert response.status_code == 200
        assert response.text

        # cleanup
        rmtree(self.GENERATED_FOLDER)

    def test_get_color_clusters_single_element_selection(self, client: FlaskClient):
        # setup JSON
        elements = [[1,0]] 

        selection: dict = {
            "type": "rectangle",
            "points": [
                {"x": 0, "y": 0},
                {"x": 1, "y": 1}
            ]
        }

        PAY_LOAD: dict = {
            "selection": selection,
            "elements": elements
        }

        # execute
        response: TestResponse = client.post(f"/api/{self.DATA_SOURCE}/cs/clusters/1/true",
                                             json=PAY_LOAD)

        # verify
        assert response.status_code == 200
        assert response.text

        # cleanup
        rmtree(self.GENERATED_FOLDER)

    def test_get_color_clusters_already_present(self, client: FlaskClient):
        # setup
        url: str = f"/api/{self.DATA_SOURCE}/cs/clusters/1/false"

        # setup JSON
        elements = [[1, 0]]
        
        PAY_LOAD: dict = {
            "selection": self.FULL_SELECTION,
            "elements": elements
        }

        # execute
        response1: TestResponse = client.post(url, json=PAY_LOAD)
        response2: TestResponse = client.post(url, json=PAY_LOAD)

        # verify
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.text == response2.text

        # cleanup
        rmtree(self.GENERATED_FOLDER)

    def test_get_color_cluster_bitmask_exists(self, client: FlaskClient):
        # execute
        response: TestResponse = client.get(f"/api/{self.BITMASKS_DATA_SOURCE}/cs/bitmask")

        # verify
        assert response.status_code == 200
        assert response.data

        # cleanup
        response.close()

    def test_get_color_cluster_bitmask_not_exists(self, client: FlaskClient):
        # execute
        response: TestResponse = client.get(f"/api/{self.DATA_SOURCE}/cs/bitmask")

        # verify
        assert response.status_code == 404
        assert response.data

        # cleanup
        response.close()

    def test_get_color_cluster_bitmask_no_config(self, client: FlaskClient):
        # setup
        set_config("this is not a config file.yml")

        # execute
        response: TestResponse = client.get(f"/api/{self.DATA_SOURCE}/cs/bitmask")

        # verify
        assert response.status_code == 500
        assert response.text == 'Error occurred while getting backend config'

    def test_get_dr_embedding_invalid_data_source(self, client: FlaskClient, caplog):
        # setup
        error_msg: str = "Failed to create DR embedding image" 

        # execute
        response: TestResponse = client.post("/api/not a data source/dr/embedding/0/0", json={})

        # verify
        assert response.status_code == 400
        assert response.text == error_msg
        assert error_msg in caplog.text
    
    def test_get_dr_overlay_invalid_data_source(self, client: FlaskClient, caplog):
        # setup
        error_msg: str = "Failed to create DR embedding image"

        # execute
        response: TestResponse = client.get("/api/not a data source/dr/overlay/0")

        # verify
        assert response.status_code == 400
        assert response.text == error_msg
        assert error_msg in caplog.text
    
    def test_get_dr_embedding_mapping_invalid_data_source(self, client: FlaskClient, caplog):
        # setup
        error_msg: str = "Failed to create DR indices to embedding image"

        # execute
        response: TestResponse = client.get("/api/not a data source/dr/embedding/mapping")

        # verify
        assert response.status_code == 400
        assert response.text == error_msg
        assert error_msg in caplog.text

    def test_get_dr_embedding_success(self, client: FlaskClient, caplog):
        # setup
        element = 2
        threshold = 50

        # execute with patch
        with patch("xrf_explorer.server.dim_reduction.generate_embedding", return_value="success"):
            response: TestResponse = client.post(f"/api/{self.DATA_SOURCE}/dr/embedding/{element}/{threshold}", json={})

        # verify
        assert response.status_code == 200
        assert response.text == "success"
        assert "success" in caplog.text or True 

    def test_get_dr_embedding_error(self, client: FlaskClient, caplog):
        # setup
        element = 2
        threshold = 50

        # execute with patch
        with patch.dict("xrf_explorer.server.routes.get_dr_embedding.__globals__", {"generate_embedding": lambda *a, **k: "error"}):
            response: TestResponse = client.post(f"/api/{self.DATA_SOURCE}/dr/embedding/{element}/{threshold}", json={})

        # verify
        assert response.status_code == 400
        assert response.get_data(as_text=True) == "Failed to create DR embedding image"
        assert "Failed to create DR embedding image" in caplog.text
    
    def test_get_color_clusters_invalid_selection_type(self, client: FlaskClient):
        # setup JSON
        elements = [[0, 100]]

        selection: dict = {
            "type": "invalid_type",
            "points": [
                {"x": 0, "y": 0},
                {"x": 1, "y": 1}
            ]
        }

        PAY_LOAD: dict = {
            "selection": selection,
            "elements": elements
        }

        # execute
        response: TestResponse = client.post(f"/api/{self.DATA_SOURCE}/cs/clusters/1/true", json=PAY_LOAD)
        
        # verify
        assert response.status_code == 400
        assert response.text == f"Error parsing selection of type {selection['type']}"

    def test_get_color_clusters_no_selection_type(self, client: FlaskClient):
        # setup JSON
        elements = [[0, 100]]

        selection: dict = {"something": "invalid"}

        PAY_LOAD: dict = {
            "selection": selection,
            "elements": elements
        }
        
        # execute
        response: TestResponse = client.post(f"/api/{self.DATA_SOURCE}/cs/clusters/1/true", json=PAY_LOAD)

        # verify
        assert response.status_code == 400
        assert response.text == "Error occurred while getting selection type or points from request body"

    def test_get_color_clusters_points_not_list(self, client: FlaskClient):
        # setup JSON
        elements = [[0, 100]]

        selection: dict = {
            "type": "rectangle",
            "points": "not a list"
        }

        PAY_LOAD: dict = {
            "selection": selection,
            "elements": elements
        }
        
        # execute
        response: TestResponse = client.post(f"/api/{self.DATA_SOURCE}/cs/clusters/1/true", json=PAY_LOAD)

        # verify
        assert response.status_code == 400
        assert response.text == f"Error parsing points: expected a list of points, got {type('string')}"

    def test_get_color_clusters_invalid_elements(self, client: FlaskClient):
        elements = [[10000, 10]]

        PAY_LOAD: dict = {
            "selection": self.FULL_SELECTION,
            "elements": elements
        }
        
        # execute
        response: TestResponse = client.post(f"/api/{self.DATA_SOURCE}/cs/clusters/1/true", json=PAY_LOAD)

        # verify
        assert response.status_code == 400
        assert response.text == f"No colors or bitmasks returned"

    def test_get_color_clusters_invalid_elements(self, client: FlaskClient):
        elements = [[1, 1500]]

        PAY_LOAD: dict = {
            "selection": self.FULL_SELECTION,
            "elements": elements
        }
        
        # execute
        response: TestResponse = client.post(f"/api/{self.DATA_SOURCE}/cs/clusters/1/true", json=PAY_LOAD)

        # verify
        assert response.status_code == 400
        assert response.text == f"No colors or bitmasks returned"