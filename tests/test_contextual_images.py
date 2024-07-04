import logging

from os.path import join, abspath

import PIL
import numpy as np

from PIL import ImageChops
from PIL.Image import Image

from xrf_explorer.server.file_system.helper import set_config
from xrf_explorer.server.file_system.workspace.contextual_images import (
    get_contextual_image_path, get_contextual_image_size,
    get_contextual_image, get_contextual_image_recipe_path,
    get_path_to_base_image
)


class TestContextualImages:
    RESOURCES_PATH: str = join('tests', 'resources')
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, "configs", "contextual-images.yml")
    TEST_IMAGE_PATH: str = abspath(join(RESOURCES_PATH, "contextual_images", "painting", "test.png"))
    TEST_RECIPE_PATH: str = abspath(join(RESOURCES_PATH, "contextual_images", "painting", "recipe.csv"))
    INVALID_IMAGE_PATH: str = abspath(join(RESOURCES_PATH, "contextual_images", "painting", "invalid.png"))
    NONEXISTENT_IMAGE_PATH: str = abspath(
        join(RESOURCES_PATH, "contextual_images", "painting", "nonexistent.png"))

    def test_get_contextual_image_path_base(self, caplog):
        caplog.set_level(logging.INFO)

        # Setup
        set_config(self.CUSTOM_CONFIG_PATH)

        # Execute
        result: str | None = get_contextual_image_path("painting", "TEST")

        # Verify
        assert result == abspath(self.TEST_IMAGE_PATH)
        assert "TEST in data source painting" in caplog.text
    
    def test_get_contextual_image_path_invalid_config(self, caplog):
        caplog.set_level(logging.INFO)

        # Setup
        set_config("invalid_config")

        # Execute
        result: str | None = get_contextual_image_path("painting", "TEST")

        # Verify
        assert result is None
        assert "Config file is empty" in caplog.text
    
    def test_get_contextual_image_path_invalid_painting(self, caplog):
        caplog.set_level(logging.INFO)

        # Setup
        set_config(self.CUSTOM_CONFIG_PATH)

        # Execute
        result: str | None = get_contextual_image_path("fake_painting", "fake_image")

        # Verify
        assert result is None

    def test_get_contextual_image_path_contextual(self, caplog):
        caplog.set_level(logging.INFO)

        # Setup
        set_config(self.CUSTOM_CONFIG_PATH)

        # Execute
        result: str | None = get_contextual_image_path("painting", "TEST2")

        # Verify
        assert result == abspath(self.TEST_IMAGE_PATH)
        assert "TEST2 in data source painting" in caplog.text

    def test_get_contextual_image_path_nonexistent(self, caplog):
        caplog.set_level(logging.INFO)

        # Setup
        set_config(self.CUSTOM_CONFIG_PATH)

        # Execute
        result: str | None = get_contextual_image_path("painting", "FAKE")

        # Verify
        assert result is None
        assert "FAKE in data source painting" in caplog.text
        assert "Could not find contextual image" in caplog.text

    def test_get_contextual_image_recipe_path_base(self, caplog):
        caplog.set_level(logging.INFO)

        # Execute
        result: str | None = get_contextual_image_recipe_path("painting", "TEST")

        # Verify
        assert result is None
        assert "no configured recipe location" in caplog.text

    def test_get_contextual_image_recipe_path_contextual(self, caplog):
        caplog.set_level(logging.INFO)

        # Execute
        result: str | None = get_contextual_image_recipe_path("painting", "TEST2")

        # Verify
        assert result == abspath(self.TEST_RECIPE_PATH)
        assert "TEST2 in data source painting" in caplog.text

    def test_get_contextual_image_recipe_path_nonexistent(self, caplog):
        caplog.set_level(logging.INFO)

        # Execute
        result: str | None = get_contextual_image_recipe_path("painting", "FAKE")

        # Verify
        assert result is None
        assert "FAKE in data source painting" in caplog.text
        assert "Could not find contextual image" in caplog.text

    def test_get_contextual_image_image(self):
        # Setup
        correct = PIL.Image.open(self.TEST_IMAGE_PATH)
        set_config(self.CUSTOM_CONFIG_PATH)

        # Execute
        result: Image | None = get_contextual_image(self.TEST_IMAGE_PATH)

        # Verify
        # Compare the images.
        assert result
        assert np.sum(np.array(ImageChops.difference(correct, result).getdata())) == 0

    def test_get_contextual_image_image_invalid(self, caplog):
        caplog.set_level(logging.INFO)

        # Execute
        result: Image | None = get_contextual_image(self.INVALID_IMAGE_PATH)

        # Verify
        assert result is None
        assert "PIL could not open" in caplog.text

    def test_get_contextual_image_image_nonexistent(self, caplog):
        caplog.set_level(logging.INFO)

        # Execute
        result: Image | None = get_contextual_image(self.NONEXISTENT_IMAGE_PATH)

        # Verify
        assert result is None
        assert "not found" in caplog.text

    def test_get_contextual_image_size(self):
        # Execute
        result: tuple[int, int] | None = get_contextual_image_size(self.TEST_IMAGE_PATH)

        # Verify
        assert result == (200, 150)

    def test_get_contextual_image_invalid_size(self):
        # Execute
        result: tuple[int, int] | None = get_contextual_image_size(self.INVALID_IMAGE_PATH)

        # Verify
        assert result is None

    def test_get_contextual_image_nonexistent_size(self):
        # Execute
        result: tuple[int, int] | None = get_contextual_image_size(self.NONEXISTENT_IMAGE_PATH)

        # Verify
        assert result is None

    def test_get_path_to_base_image(self):
        # Setup
        set_config(self.CUSTOM_CONFIG_PATH)

        # Execute
        result: str | None = get_path_to_base_image("painting")

        # Verify
        assert abspath(result) == abspath(self.TEST_IMAGE_PATH)
