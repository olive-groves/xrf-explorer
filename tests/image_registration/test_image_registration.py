import pytest
from os import remove
from os.path import exists
from xrf_explorer.server.image_register import register_image_to_image
from xrf_explorer.server.image_register.register_image import (
    register_image_to_data_cube,
)


class TestImageRegistration:
    PATH_IMAGE_REFERENCE = "tests/resources/image_registration/image.png"
    PATH_IMAGE_REGISTER = "tests/resources/image_registration/image.png"
    PATH_CUBE = "tests/resources/image_registration/cube.dms"
    PATH_CONTROL_POINTS = "tests/resources/image_registration/control_points.csv"
    PATH_RESULT = "tests/resources/image_registration/result.tif"

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
            "some/random/non/existant/path",
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
        result: bool = register_image_to_image(
            self.PATH_IMAGE_REFERENCE,
            self.PATH_IMAGE_REGISTER,
            self.PATH_CONTROL_POINTS,
            "tests/resources/image_registration/unexistantdir/result.tif",
        )

        assert not result
        assert not exists(self.PATH_RESULT)

        assert (
            "Registered image could not be saved at tests/resources/image_registration/unexistantdir because directory does not exist."
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
        result: bool = register_image_to_data_cube(
            "made/up/path", self.PATH_IMAGE_REGISTER, self.PATH_RESULT
        )

        assert not result
        assert not exists(self.PATH_RESULT)

        assert "Data cube not found at made/up/path" in caplog.text

    def test_register_image_to_cube_image_register_not_found(self, caplog):
        result: bool = register_image_to_data_cube(
            self.PATH_CUBE, "made/up/path", self.PATH_RESULT
        )

        assert not result
        assert not exists(self.PATH_RESULT)

        assert "Image for registering not found at made/up/path" in caplog.text

    def test_register_image_to_cube_destination_not_found(self, caplog):
        result: bool = register_image_to_data_cube(
            self.PATH_CUBE,
            self.PATH_IMAGE_REGISTER,
            "tests/resources/image_registration/unexistantdir/result.tif",
        )

        assert not result
        assert not exists(self.PATH_RESULT)

        assert (
            "Registered image could not be saved at tests/resources/image_registration/unexistantdir/result.tif because directory does not exist."
            in caplog.text
        )

    def test_register_image_to_cube_success(self, caplog):
        result: bool = register_image_to_data_cube(
            self.PATH_CUBE, self.PATH_IMAGE_REGISTER, self.PATH_RESULT
        )

        assert result
        assert exists(self.PATH_RESULT)
