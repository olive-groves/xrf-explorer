import os
from xrf_explorer.server.image_register import register_image_to_image


class TestImageRegistration:
    PATH_IMAGE_REFERENCE = "../resources/image_registration/196_1989_RGB.tif"
    PATH_IMAGE_REGISTER = "../resources/image_registration/196_1989_RGB.tif"
    PATH_CUBE = "../resources/image_registration/cube.dms"
    PATH_CONTROL_POINTS = "../resources/image_registration/control_points.csv"
    PATH_RESULT = "../resources/image_registration/result.tif"

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

        assert "Reference image could not be loaded" in caplog.text
        # assert "Image for registering could not be loaded" in caplog.text
