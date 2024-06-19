import logging

from os import remove
from os.path import join, exists

import pytest

from cv2.typing import MatLike

from xrf_explorer.server.file_system import set_config
from xrf_explorer.server.process.image_registration import register_image_to_image, get_image_registered_to_data_cube


class TestImageRegistration:
    CONFIG_PATH = "tests/resources/configs/image-registration.yml"

    PATH_IMAGE_REFERENCE = "tests/resources/image_registration/data_source/image.png"
    PATH_IMAGE_REGISTER = "tests/resources/image_registration/data_source/image.png"
    PATH_CUBE = "tests/resources/image_registration/data_source/cube.dms"
    PATH_CONTROL_POINTS = "tests/resources/image_registration/data_source/control_points.csv"
    PATH_RESULT = "tests/resources/image_registration/result.tif"

    DATA_SOURCE = "data_source"
    IMAGE_NAME = "RGB"

    @pytest.fixture(autouse=True)
    def setup_environment(self):
        if exists(self.PATH_RESULT):
            remove(self.PATH_RESULT)

        yield

    def test_register_image_to_image_reference_not_found(self, caplog):
        result: bool = register_image_to_image(
            "made/up/path",
            self.PATH_IMAGE_REGISTER,
            self.PATH_CUBE,
            self.PATH_RESULT,
        )

        assert not result
        assert not exists(self.PATH_RESULT)

        assert "Reference image could not be loaded" in caplog.text

    def test_register_image_to_image_register_not_found(self, caplog):
        result: bool = register_image_to_image(
            self.PATH_IMAGE_REFERENCE,
            "some/random/non/existent/path",
            self.PATH_CUBE,
            self.PATH_RESULT,
        )

        assert not result
        assert not exists(self.PATH_RESULT)

        assert "Image for registering could not be loaded" in caplog.text

    def test_register_image_to_image_csv_not_found(self, caplog):
        result: bool = register_image_to_image(
            self.PATH_IMAGE_REFERENCE,
            self.PATH_IMAGE_REGISTER,
            "made/up/path",
            self.PATH_RESULT,
        )

        assert not result
        assert not exists(self.PATH_RESULT)

        assert "Control points file could not be found at made/up/path" in caplog.text

    def test_register_image_to_image_destination_not_found(self, caplog):
        # setup
        invalid_path: str = "tests/resources/image_registration/unexistantdir"

        # execute
        result: bool = register_image_to_image(
            self.PATH_IMAGE_REFERENCE,
            self.PATH_IMAGE_REGISTER,
            self.PATH_CONTROL_POINTS,
            join(invalid_path, "result.tif"),
        )

        # verify
        assert not result
        assert not exists(self.PATH_RESULT)
        assert (
                f"Registered image could not be saved at {invalid_path} because directory does not exist."
                in caplog.text
        )

    def test_register_image_to_image_success(self, caplog):
        result: bool = register_image_to_image(
            self.PATH_IMAGE_REFERENCE,
            self.PATH_IMAGE_REGISTER,
            self.PATH_CONTROL_POINTS,
            self.PATH_RESULT,
        )

        assert result
        assert exists(self.PATH_RESULT)

    def test_register_image_to_cube_data_cube_not_found(self, caplog):
        # setup 
        set_config(self.CONFIG_PATH)

        # execute
        result: MatLike | None = get_image_registered_to_data_cube(
            "not_a_data_source", self.IMAGE_NAME
        )

        # verify
        assert result is None
        assert "Data cube not found at" in caplog.text

    def test_register_image_to_cube_image_register_not_found(self, caplog):
        # setup
        set_config(self.CONFIG_PATH)

        # execute
        result: MatLike | None = get_image_registered_to_data_cube(
            self.DATA_SOURCE, "not_an_image_name"
        )

        # verify
        assert result is None
        assert "Image for registering not found at" in caplog.text

    def test_register_image_to_cube_success(self, caplog):
        # setup
        set_config(self.CONFIG_PATH)
        caplog.set_level(logging.INFO)

        # execute
        result: MatLike | None = get_image_registered_to_data_cube(
            self.DATA_SOURCE, self.IMAGE_NAME
        )

        # verify
        assert result is not None
        assert result.shape == (3, 3, 3)
        assert "Removing columns: 1"
        assert "Registering image to elemental cube" in caplog.text
