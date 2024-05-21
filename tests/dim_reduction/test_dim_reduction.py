import logging

import sys

from os.path import join
from pathlib import Path

sys.path.append('.')

from xrf_explorer.server.dim_reduction.embedding import generate_embedding
from xrf_explorer.server.dim_reduction.overlay import create_embedding_image

RESOURCES_PATH: Path = Path('tests', 'resources')


class TestDimReduction:
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, Path('configs', 'dim-reduction.yml'))
    CUSTOM_CONFIG_PATH_NO_EMBEDDING: str = join(RESOURCES_PATH, Path('configs', 'dim-reduction-no-embedding.yml'))
    TEMP_FOLDER: str = join(RESOURCES_PATH, 'dim_reduction', 'dim_reduction')

    def test_config_not_found(self, caplog):
        # setup
        element: int = 9
        threshold: int = 100
        overlay_type: str = 'rgb'

        # execute
        result1: bool = generate_embedding(element, threshold, config_path='this-config-does-not-exist.yml')
        result2: str = create_embedding_image(overlay_type, config_path='this-config-does-not-exist.yml')

        # verify
        assert not result1
        assert not result2

        # verify log messages
        assert 'Failed to access config' in caplog.text

    def test_invalid_element_generating(self, caplog):
        # setup
        element1: int = -1
        element2: int = 1000000
        threshold: int = 100

        # execute
        result1: bool = generate_embedding(element1, threshold, config_path=self.CUSTOM_CONFIG_PATH)
        result2: bool = generate_embedding(element2, threshold, config_path=self.CUSTOM_CONFIG_PATH)

        # verify
        assert not result1
        assert not result2

        # verify log messages
        assert 'Invalid element: -1' in caplog.text
        assert 'Invalid element: 1000000' in caplog.text

    def test_invalid_element_creating_image(self, caplog):
        # setup
        overlay_type1: str = '-1'
        overlay_type2: str = '1000000'

        # execute
        result1: str = create_embedding_image(overlay_type1, config_path=self.CUSTOM_CONFIG_PATH)
        result2: str = create_embedding_image(overlay_type2, config_path=self.CUSTOM_CONFIG_PATH)

        # verify
        assert not result1
        assert not result2

        # verify log messages
        assert 'Invalid element: -1' in caplog.text
        assert 'Invalid element: 1000000' in caplog.text

    def test_invalid_umap(self, caplog):
        # setup
        element: int = 2
        threshold: int = 100
        umap_args: dict[str, str] = {"n-neighbors": '0', "min-dist": '0', "n-components": '0', "metric": "invalid"}

        # execute
        result: bool = generate_embedding(element, threshold, umap_parameters=umap_args,
                                          config_path=self.CUSTOM_CONFIG_PATH)

        # verify
        assert not result

        # verify log messages
        assert 'Failed to compute embedding' in caplog.text

    def test_no_embedding(self, caplog):
        # setup
        overlay_type: str = '1'

        # execute
        result: str = create_embedding_image(overlay_type, config_path=self.CUSTOM_CONFIG_PATH_NO_EMBEDDING)

        # verify
        assert not result

        # verify log messages
        assert 'Failed to load indices and/or embedding data.' in caplog.text

    def test_valid_embedding(self, caplog):
        caplog.set_level(logging.INFO)

        # setup
        element: int = 2
        threshold: int = 0
        umap_args: dict[str, str] = {"n-neighbors": '2', "metric": "euclidean"}

        # execute
        result: bool = generate_embedding(element, threshold, umap_parameters=umap_args,
                                          config_path=self.CUSTOM_CONFIG_PATH)

        # verify
        assert result

        # verify log messages
        assert 'Generated embedding successfully' in caplog.text

    def test_high_threshold(self, caplog):
        # setup
        element: int = 2
        threshold: int = 1000
        umap_args: dict[str, str] = {"n-neighbors": '2', "metric": "euclidean"}

        # execute
        result: bool = generate_embedding(element, threshold, umap_parameters=umap_args,
                                          config_path=self.CUSTOM_CONFIG_PATH)

        # verify
        assert not result

        # verify log messages
        assert 'Failed to compute embedding' in caplog.text

    def test_valid_image(self, caplog):
        caplog.set_level(logging.INFO)

        # setup
        overlay_type: str = '1'

        # setup - generate embedding
        element: int = 2
        threshold: int = 0
        umap_args: dict[str, str] = {"n-neighbors": '2', "metric": "euclidean"}
        result: bool = generate_embedding(element, threshold, umap_parameters=umap_args,
                                          config_path=self.CUSTOM_CONFIG_PATH)

        # execute
        result: bool = create_embedding_image(overlay_type, config_path=self.CUSTOM_CONFIG_PATH)

        # verify
        assert result

        # verify log messages
        assert 'Created embedding image successfully' in caplog.text
