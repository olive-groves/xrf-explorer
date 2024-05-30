import logging
import sys
from os.path import join, normpath, abspath
from pathlib import Path

import PIL
import numpy as np
from PIL import ImageChops
from PIL.Image import Image
from cv2 import imread

sys.path.append('.')

from xrf_explorer.server.file_system.contextual_images import get_contextual_image, get_contextual_image_path, \
    get_contextual_image_size

RESOURCES_PATH: Path = Path('tests', 'resources')


def are_images_identical(image1: Image, image2: Image) -> bool:
    # Compare the images.
    return np.sum(np.array(ImageChops.difference(image1, image2).getdata())) == 0


class TestContextualImages:
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, Path("configs", "contextual-images.yml"))
    TEST_IMAGE_PATH: str = abspath(join(RESOURCES_PATH, Path("contextual_images", "painting", "test.png")))
    INVALID_IMAGE_PATH: str = abspath(join(RESOURCES_PATH, Path("contextual_images", "painting", "invalid.png")))
    NONEXISTENT_IMAGE_PATH: str = abspath(join(RESOURCES_PATH, Path("contextual_images", "painting", "nonexistent.png")))

    def test_get_contextual_image_path_base(self, caplog):
        caplog.set_level(logging.INFO)

        # Execute
        result = get_contextual_image_path("painting", "TEST", self.CUSTOM_CONFIG_PATH)

        # Verify
        assert result == abspath(self.TEST_IMAGE_PATH)

    def test_get_contextual_image_path_contextual(self, caplog):
        caplog.set_level(logging.INFO)

        # Execute
        result = get_contextual_image_path("painting", "TEST2", self.CUSTOM_CONFIG_PATH)

        # Verify
        assert result == abspath(self.TEST_IMAGE_PATH)

    def test_get_contextual_image_path_nonexistent(self, caplog):
        caplog.set_level(logging.INFO)

        # Execute
        result = get_contextual_image_path("painting", "FAKE", self.CUSTOM_CONFIG_PATH)

        # Verify
        assert result is None

    def test_get_contextual_image(self, caplog):
        caplog.set_level(logging.INFO)

        # Setup
        correct = PIL.Image.open(self.TEST_IMAGE_PATH)

        # Execute
        result = get_contextual_image(self.TEST_IMAGE_PATH)

        # Verify
        assert are_images_identical(correct, result)

    def test_get_contextual_image_invalid(self, caplog):
        caplog.set_level(logging.INFO)

        # Execute
        result = get_contextual_image(self.INVALID_IMAGE_PATH)

        # Verify
        assert result is None

    def test_get_contextual_image_nonexistent(self, caplog):
        caplog.set_level(logging.INFO)

        # Execute
        result = get_contextual_image(self.NONEXISTENT_IMAGE_PATH)

        # Verify
        assert result is None

    def test_get_contextual_image_size(self, caplog):
        caplog.set_level(logging.INFO)

        # Setup
        correct = PIL.Image.open(self.TEST_IMAGE_PATH)

        # Execute
        result = get_contextual_image_size(self.TEST_IMAGE_PATH)

        # Verify
        assert result == (200, 150)

    def test_get_contextual_image_invalid_size(self, caplog):
        caplog.set_level(logging.INFO)

        # Execute
        result = get_contextual_image_size(self.INVALID_IMAGE_PATH)

        # Verify
        assert result is None

    def test_get_contextual_image_nonexistent_size(self, caplog):
        caplog.set_level(logging.INFO)

        # Execute
        result = get_contextual_image_size(self.NONEXISTENT_IMAGE_PATH)

        # Verify
        assert result is None
