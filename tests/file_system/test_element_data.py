from logging import INFO
from json import dump
from shutil import rmtree, copytree
from os import makedirs
from os.path import join, isfile

import pytest

from numpy import ndarray, array_equal, array, float32, full

from xrf_explorer.server.file_system.cubes.convert_dms import to_dms
from xrf_explorer.server.file_system.cubes.elemental import (
    get_elemental_data_cube, get_elemental_map, get_element_names, 
    get_element_averages, convert_elemental_cube_to_dms, get_element_averages_selection
)
from xrf_explorer.server.file_system.helper import set_config, get_config

RESOURCES_PATH: str = join('tests', 'resources')


class TestElementalData:
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, 'configs', 'elemental-data.yml')
    PATH_TO_TEST_FOLDER: str = join(RESOURCES_PATH, 'file_system', 'test_elemental_data')

    SOURCE_FOLDER_CSV: str = 'csv'
    SOURCE_FOLDER_DMS: str = 'dms'
    DATA_CUBE_DMS: str = 'test.dms'
    DATA_CUBE_CSV: str = 'test.csv'

    NAME_CUBE_FROM_CSV: str = 'cube_from_csv'
    NON_EXISTING_CUBE: str = 'non-existing.dms'

    ELEMENTS: list[str] = ["Secret", "Element"]
    RAW_ELEMENTAL_CUBE: ndarray = array([
        [[-1, -2, -3], [-4, -5, -6], [-7, -8, -9]],
        [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    ], dtype=float32)

    @pytest.fixture(autouse=True)
    def setup_environment(self):
        set_config(self.CUSTOM_CONFIG_PATH)
        yield

    def do_test_get_element_names(self, source, caplog):
        caplog.set_level(INFO)

        # setup
        expected_output: str = f"Elements loaded. Total elements: {len(self.ELEMENTS)}"

        # execute
        result: list[str] = get_element_names(source)

        # verify
        assert len(result) == 2
        assert result == self.ELEMENTS
        assert expected_output in caplog.text

    def do_test_get_elemental_cube(self, source, caplog):
        caplog.set_level(INFO)

        # setup
        expected_output: str = f"Elemental data cube loaded. Shape: {self.RAW_ELEMENTAL_CUBE.shape}"

        # execute
        result: ndarray = get_elemental_data_cube(source)

        # verify
        assert array_equal(result, self.RAW_ELEMENTAL_CUBE)
        assert expected_output in caplog.text

    def do_test_get_elemental_map(self, source, caplog):
        caplog.set_level(INFO)

        # setup
        elemental_map: ndarray = self.RAW_ELEMENTAL_CUBE[0]
        expected_output: str = f"Elemental map loaded. Shape: {elemental_map.shape}"

        # load custom config
        custom_config: dict | None = get_config()
        assert custom_config is not None

        path: str = str(join(custom_config["uploads-folder"], source))

        # execute
        result: ndarray = get_elemental_map(0, path)

        # verify
        assert array_equal(result, elemental_map)
        assert expected_output in caplog.text

    def test_get_element_names(self, caplog):
        self.do_test_get_element_names(self.SOURCE_FOLDER_DMS, caplog)
        self.do_test_get_element_names(self.SOURCE_FOLDER_CSV, caplog)

    def test_get_elemental_cube(self, caplog):
        # setup
        source_folder: str = "csv"

        # execute & verify
        self.do_test_get_elemental_cube(source_folder, caplog)

    def test_get_elemental_map(self, caplog):
        # setup
        dms_path: str = join(self.SOURCE_FOLDER_DMS, self.DATA_CUBE_DMS)
        csv_path: str = join(self.SOURCE_FOLDER_CSV, self.DATA_CUBE_CSV)

        # execute & verify
        self.do_test_get_elemental_map(dms_path, caplog)
        self.do_test_get_elemental_map(csv_path, caplog)

    def test_get_element_averages(self, caplog):
        caplog.set_level(INFO)

        # setup
        expected_output: str = "Calculated the average composition of the elements."

        # execute
        result_dms: list[dict[str, str | float]] = get_element_averages(self.SOURCE_FOLDER_DMS)
        result_csv: list[dict[str, str | float]] = get_element_averages(self.SOURCE_FOLDER_CSV)

        # verify
        assert len(result_dms) == 2
        assert result_dms[0]['name'] == self.ELEMENTS[0]
        assert result_dms[1]['name'] == self.ELEMENTS[1]
        assert result_dms == result_csv
        assert expected_output in caplog.text

    def test_csv_to_dms(self, caplog):
        caplog.set_level(INFO)

        # setup
        set_config(self.CUSTOM_CONFIG_PATH)

        # create temp data source
        temp_data_source: str = 'csv_to_dms'
        path_to_temp_folder: str = join(self.PATH_TO_TEST_FOLDER, temp_data_source)
        copytree(join(self.PATH_TO_TEST_FOLDER, self.SOURCE_FOLDER_CSV), path_to_temp_folder)

        # execute
        result: bool = convert_elemental_cube_to_dms(temp_data_source, 'Datacube')

        # verify
        path_to_converted_csv_file: str = join(path_to_temp_folder, self.DATA_CUBE_CSV)
        assert result
        assert not isfile(path_to_converted_csv_file)
        assert isfile(join(path_to_temp_folder, self.DATA_CUBE_DMS))
        assert 'to .dms format.' in caplog.text

        # cleanup
        rmtree(path_to_temp_folder)

    def test_csv_to_dms_directly(self, caplog):
        # setup
        set_config(self.CUSTOM_CONFIG_PATH)
        custom_config: dict = get_config()
        folder_name: str = "from_csv"
        folder_path: str = join(custom_config["uploads-folder"], folder_name)
        makedirs(folder_path, exist_ok=True)

        workspace: dict = {
          "elementalCubes": [
            {
              "dataLocation": self.NAME_CUBE_FROM_CSV + ".dms",
              "fileType": "dms",
              "name": "Datacube",
              "recipeLocation": ""
            }
          ],
          "name": folder_name
        }
        with open(join(folder_path, 'workspace.json'), 'w') as workspace_file:
            dump(workspace, workspace_file)

        # execute
        result: bool = to_dms(folder_path, self.NAME_CUBE_FROM_CSV, self.RAW_ELEMENTAL_CUBE, self.ELEMENTS)

        # verify
        assert result
        self.do_test_get_element_names(folder_name, caplog)
        self.do_test_get_elemental_cube(folder_name, caplog)

        # cleanup
        rmtree(folder_path)

    def test_get_element_averages_selection(self, caplog):
        caplog.set_level(INFO)

        # setup
        set_config(self.CUSTOM_CONFIG_PATH)
        mask: ndarray = full((3, 3), 1)
        
        # execute
        result: list[dict[str, str | float]] = get_element_averages_selection(self.SOURCE_FOLDER_DMS, mask)

        # verify
        for i in range(len(self.ELEMENTS)):
            assert result[i]['name'] == self.ELEMENTS[i]
            assert result[i]['average'] >= 0
        assert 'Calculated the average composition of the elements within selection.' in caplog.text
