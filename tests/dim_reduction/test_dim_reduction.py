import logging

import sys

from os import remove
from os.path import isfile, join
from pathlib import Path

sys.path.append('.')

from xrf_explorer.server.dim_reduction.embedding import generate_embedding
from xrf_explorer.server.dim_reduction.overlay import create_embedding_image

RESOURCES_PATH: Path = Path('tests', 'resources')


class TestDimReduction:
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, 'configs', 'dim-reduction.yml')
    CUSTOM_CONFIG_PATH_NO_EMBEDDING: str = join(RESOURCES_PATH, 'configs', 'dim-reduction-no-embedding.yml')
    CUSTOM_CONFIG_PATH_EMBEDDING_PRESENT: str = join(RESOURCES_PATH, 'configs', 'dim-reduction-embedding-present.yml')
    TEST_DATA_SOURCE: str = 'test_data_source'
    PATH_TEST_CUBE: str = join(RESOURCES_PATH, 'dim_reduction', TEST_DATA_SOURCE, 'test_cube.dms')

    def test_config_not_found(self, caplog):
        # setup
        element: int = 9
        threshold: int = 100
        overlay_type: str = 'contextual_rgb'

        # execute
        result1: str = generate_embedding(
            self.PATH_TEST_CUBE, element, threshold, config_path='this-config-does-not-exist.yml'
        )
        result2: str = create_embedding_image(
            self.TEST_DATA_SOURCE, overlay_type, config_path='this-config-does-not-exist.yml'
        )

        # verify
        assert result1 == 'error'
        assert not result2

        # verify log messages
        assert 'Failed to access config' in caplog.text

    def test_invalid_element_generating(self, caplog):
        # setup
        element1: int = -1
        element2: int = 1000000
        threshold: int = 100

        # execute
        result1: str = generate_embedding(
            self.PATH_TEST_CUBE, element1, threshold, config_path=self.CUSTOM_CONFIG_PATH
        )
        result2: str = generate_embedding(
            self.PATH_TEST_CUBE, element2, threshold, config_path=self.CUSTOM_CONFIG_PATH
        )

        # verify
        assert result1 == 'error'
        assert result2 == 'error'

        # verify log messages
        assert 'Invalid element: -1' in caplog.text
        assert 'Invalid element: 1000000' in caplog.text

    def test_invalid_element_creating_image(self, caplog):
        # setup
        overlay_type2: str = 'elemental_1000000'

        # execute
        result2: str = create_embedding_image(
            self.TEST_DATA_SOURCE, overlay_type2, config_path=self.CUSTOM_CONFIG_PATH_EMBEDDING_PRESENT
        )

        # verify
        assert not result2

        # verify log messages
        assert 'Invalid element: 1000000' in caplog.text

    def test_invalid_umap(self, caplog):
        # setup
        element: int = 2
        threshold: int = 100
        umap_args: dict[str, str] = {"n-neighbors": '0', "min-dist": '0', "n-components": '0', "metric": "invalid"}

        # execute
        result: str = generate_embedding(self.PATH_TEST_CUBE, element, threshold, umap_parameters=umap_args,
                                          config_path=self.CUSTOM_CONFIG_PATH)

        # verify
        assert result == 'error'

        # verify log messages
        assert 'Failed to compute embedding' in caplog.text

    def test_no_embedding(self, caplog):
        # setup
        overlay_type: str = 'elemental_1'

        # execute
        result: str = create_embedding_image(
            self.TEST_DATA_SOURCE, overlay_type,
            config_path=self.CUSTOM_CONFIG_PATH_NO_EMBEDDING
        )

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
        path_generated_file: str = join(RESOURCES_PATH, 'dim_reduction', 'from_dim_reduction', 'embedded_data.npy')

        # execute
        result: str = generate_embedding(self.PATH_TEST_CUBE, element, threshold, umap_parameters=umap_args,
                                          config_path=self.CUSTOM_CONFIG_PATH)

        # verify
        assert result == 'success'
        assert isfile(path_generated_file)
        assert 'Generated embedding successfully' in caplog.text

        # cleanup
        remove(path_generated_file)

    def test_high_threshold(self, caplog):
        # setup
        element: int = 2
        threshold: int = 1000
        umap_args: dict[str, str] = {"n-neighbors": '2', "metric": "euclidean"}

        # execute
        result: str = generate_embedding(self.PATH_TEST_CUBE, element, threshold, umap_parameters=umap_args,
                                          config_path=self.CUSTOM_CONFIG_PATH)

        # verify
        assert result == 'error'

        # verify log messages
        assert 'Failed to compute embedding' in caplog.text

    def test_valid_image(self, caplog):
        caplog.set_level(logging.INFO)

        # setup
        overlay_type: str = 'elemental_1'
        path_generated_file: str = join(RESOURCES_PATH, 'dim_reduction', 'embedding_present', 'embedding.png')

        # execute
        result: str = create_embedding_image(self.TEST_DATA_SOURCE, overlay_type, config_path=self.CUSTOM_CONFIG_PATH_EMBEDDING_PRESENT)

        # verify
        assert result
        assert isfile(path_generated_file)
        assert 'Created embedding image successfully' in caplog.text

        # cleanup
        remove(path_generated_file)
