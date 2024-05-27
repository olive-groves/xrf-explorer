import logging
import os.path
import sys
from os.path import join, normpath
from pathlib import Path

import numpy as np
from cv2 import imread

sys.path.append('.')

from xrf_explorer.server.contextual_images import set_contextual_image, get_contextual_image

RESOURCES_PATH: Path = Path('tests', 'resources')


def are_images_identical(file_path1: str, file_path2: str):
    img1: np.array = imread(file_path1)
    img2: np.array = imread(file_path2)

    # Check if images are of the same shape, if not, return False.
    if img1.shape != img2.shape:
        return False

    # Compare the images.
    return np.array_equal(img1, img2)


class TestColorSegmentation:
    TEST_IMAGE_PATH: str = join(RESOURCES_PATH, Path('contextual_images', 'test.png'))
    INVALID_FILE_TYPE_PATH: str = join(RESOURCES_PATH, Path("contextual_images", "invalid_file_type.txt"))
    FAKE_FILE_PATH: str = join(RESOURCES_PATH, Path("contextual_images", "fake_path.png"))

    def test_set_contextual_image(self, caplog):
        caplog.set_level(logging.INFO)

        # Set-up
        image_path: str = str(Path("xrf_explorer", "server", "temp", "contextual_images", "contextual_image.png"))

        # Execute
        set_contextual_image(self.TEST_IMAGE_PATH)

        # Verify
        assert os.path.exists(image_path)  # Verify that the file exists.
        assert are_images_identical(image_path, self.TEST_IMAGE_PATH)  # Check if images are the same.

        # Verify log message
        assert "Contextual image saved successfully." in caplog.text

    def test_invalid_file_type_set(self, caplog):

        # Set-up
        image_path: str = str(Path("xrf_explorer", "server", "temp", "contextual_images", "contextual_image.txt"))

        # Execute
        set_contextual_image(self.INVALID_FILE_TYPE_PATH)

        # Verify
        assert not os.path.exists(image_path)  # Verify that the file does not exist.

        # Verify log message
        assert "The provided file has an invalid type." in caplog.text

    def test_invalid_file_path_set(self, caplog):

        # Execute
        set_contextual_image(self.FAKE_FILE_PATH)

        # Verify log message
        assert f"The file at path {self.FAKE_FILE_PATH} does not exist." in caplog.text

    def test_get_contextual_image(self, caplog):
        caplog.set_level(logging.INFO)

        # Set-up
        image_path: str = str(Path("xrf_explorer", "server", "temp", "contextual_images", "contextual_image.png"))
        image_path: str = normpath(image_path)

        # Execute
        result1: str = get_contextual_image("png")
        result2: str = get_contextual_image(".png")
        result3: str = get_contextual_image("PNG")
        result4: str = get_contextual_image(".PNG")

        # Verify
        assert result1 == image_path
        assert result2 == image_path
        assert result3 == image_path
        assert result4 == image_path

        # Verify log message
        assert "Contextual image found." in caplog.text

    def test_invalid_file_type_get(self, caplog):

        # Execute
        result1: str = get_contextual_image("fake")
        result2: str = get_contextual_image(".fake")
        result3: str = get_contextual_image("FAKE")
        result4: str = get_contextual_image(".FAKE")

        # Verify
        assert result1 == ""
        assert result2 == ""
        assert result3 == ""
        assert result4 == ""

        # Verify log message
        assert "The provided file type is invalid." in caplog.text

    def test_file_not_found_get(self, caplog):

        # NOTE: This test only works if no JPG contextual image has been set.

        # Execute
        result: str = get_contextual_image("jpg")

        # Verify
        assert result == ""

        # verify log message
        assert "File was not found." in caplog.text
