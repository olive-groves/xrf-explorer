import os
from os.path import exists
from xrf_explorer.server.image_register import register_image_to_image


class TestImageRegistration:
    PATH_IMAGE_REFERENCE = "tests/resources/image_registration/196_1989_RGB.tif"
    PATH_IMAGE_REGISTER = "tests/resources/image_registration/196_1989_RGB.tif"
    PATH_CUBE = "tests/resources/image_registration/cube.dms"
    PATH_CONTROL_POINTS = "tests/resources/image_registration/control_points.csv"
    PATH_RESULT = "tests/resources/image_registration/result.tif"

    def test_register_image_to_image_reference_not_found(self, caplog):
        result: bool = register_image_to_image(
            "made/up/path",
            self.PATH_IMAGE_REGISTER,
            self.PATH_CUBE,
            self.PATH_RESULT,
        )

        assert not result

        assert "Reference image could not be loaded" in caplog.text

    def test_register_image_to_image_register_not_found(self, caplog):
        result: bool = register_image_to_image(
            self.PATH_IMAGE_REFERENCE,
            "some/random/non/existant/path",
            self.PATH_CUBE,
            self.PATH_RESULT,
        )

        assert not result

        assert "Image for registering could not be loaded" in caplog.text

    def test_register_image_to_image_csv_not_found(self, caplog):
        result: bool = register_image_to_image(
            self.PATH_IMAGE_REFERENCE,
            self.PATH_IMAGE_REGISTER,
            "made/up/path",
            self.PATH_RESULT,
        )

        assert not result

        assert "Control points file could not be found at made/up/path" in caplog.text

    def test_register_image_to_image_creation_dir_not_found(self, caplog):
        result: bool = register_image_to_image(
            self.PATH_IMAGE_REFERENCE,
            self.PATH_IMAGE_REGISTER,
            self.PATH_CONTROL_POINTS,
            "tests/resources/image_registration/unexistantdir/result.tif",
        )

        assert not result

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

        does_file_exist: bool = exists(self.PATH_RESULT)

        assert result
        assert does_file_exist
