import logging

import sys

from os import remove
from os.path import isfile, join
from pathlib import Path

from xrf_explorer.server.file_system.config_handler import set_config

sys.path.append('.')

from xrf_explorer.server.dim_reduction import (
    generate_embedding, create_embedding_image, get_image_of_indices_to_embedding
)

RESOURCES_PATH: Path = Path('tests', 'resources')


class TestDimReduction:
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, 'configs', 'dim-reduction.yml')
    CUSTOM_CONFIG_PATH_NO_EMBEDDING: str = join(RESOURCES_PATH, 'configs', 'dim-reduction-no-embedding.yml')
    CUSTOM_CONFIG_PATH_EMBEDDING_PRESENT: str = join(RESOURCES_PATH, 'configs', 'dim-reduction-embedding-present.yml')
    TEST_DATA_SOURCE: str = 'test_data_source'
    PATH_TEST_CUBE: str = join(RESOURCES_PATH, 'dim_reduction', TEST_DATA_SOURCE, 'test_cube.dms')
    PATH_GENERATED_FOLDER: str = join(RESOURCES_PATH, 'dim_reduction', TEST_DATA_SOURCE, 'from_dim_reduction')

    def test_config_not_found(self, caplog):
        # setup
        element: int = 9
        threshold: int = 100
        overlay_type: str = 'contextual_rgb'
        set_config('this-config-does-not-exist.yml')

        # execute
        result1: str = generate_embedding(
            self.TEST_DATA_SOURCE, element, threshold
        )
        result2: str = create_embedding_image(
            self.TEST_DATA_SOURCE, overlay_type
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
        set_config(self.CUSTOM_CONFIG_PATH)

        # execute
        result1: str = generate_embedding(self.TEST_DATA_SOURCE, element1, threshold)
        result2: str = generate_embedding(self.TEST_DATA_SOURCE, element2, threshold)

        # verify
        assert result1 == 'error'
        assert result2 == 'error'

        # verify log messages
        assert 'Invalid element: -1' in caplog.text
        assert 'Invalid element: 1000000' in caplog.text

    def test_invalid_element_creating_image(self, caplog):
        # setup
        overlay_type: str = 'elemental_1000000'
        set_config(self.CUSTOM_CONFIG_PATH_EMBEDDING_PRESENT)

        # execute
        result: str = create_embedding_image(self.TEST_DATA_SOURCE, overlay_type)

        # verify
        assert not result

        # verify log messages
        assert 'Invalid element: 1000000' in caplog.text

    def test_invalid_umap(self, caplog):
        # setup
        element: int = 2
        threshold: int = 100
        umap_args: dict[str, str] = {'n-neighbors': '0', 'min-dist': '0', 'n-components': '0', 'metric': 'invalid'}
        set_config(self.CUSTOM_CONFIG_PATH)

        # execute
        result: str = generate_embedding(self.TEST_DATA_SOURCE, element, threshold, new_umap_parameters=umap_args)

        # verify
        assert result == 'error'

        # verify log messages
        assert 'Failed to compute embedding' in caplog.text

    def test_no_embedding(self, caplog):
        # setup
        overlay_type: str = 'elemental_1'
        set_config(self.CUSTOM_CONFIG_PATH_NO_EMBEDDING)

        # execute
        result: str = create_embedding_image(self.TEST_DATA_SOURCE, overlay_type)

        # verify
        assert not result

        # verify log messages
        assert 'Failed to load indices and/or embedding data.' in caplog.text

    def test_valid_embedding(self, caplog):
        caplog.set_level(logging.INFO)

        # setup
        element: int = 2
        threshold: int = 0
        umap_args: dict[str, str] = {'n-neighbors': '2', 'metric': 'euclidean'}
        path_generated = join(
            RESOURCES_PATH, 'dim_reduction', self.TEST_DATA_SOURCE, 'generated', 'from_dim_reduction'
        )
        path_embedding: str = join(path_generated, 'embedded_data.npy')
        path_indices: str = join(path_generated, 'indices.npy')
        set_config(self.CUSTOM_CONFIG_PATH)

        # execute
        result: str = generate_embedding(self.TEST_DATA_SOURCE, element, threshold, new_umap_parameters=umap_args)

        # verify
        assert result == 'success'
        assert isfile(path_embedding)
        assert isfile(path_indices)
        assert 'Generated embedding successfully' in caplog.text

        # cleanup
        remove(path_embedding)
        remove(path_indices)

    def test_high_threshold(self, caplog):
        # setup
        element: int = 2
        threshold: int = 1000
        umap_args: dict[str, str] = {'n-neighbors': '2', 'metric': 'euclidean'}
        set_config(self.CUSTOM_CONFIG_PATH)

        # execute
        result: str = generate_embedding(self.TEST_DATA_SOURCE, element, threshold, new_umap_parameters=umap_args)

        # verify
        assert result == 'error'

        # verify log messages
        assert 'Failed to compute embedding' in caplog.text

    def test_valid_image(self, caplog):
        caplog.set_level(logging.INFO)

        # setup
        overlay_type: str = 'elemental_1'
        path_generated_folder: str = join(
            RESOURCES_PATH, 'dim_reduction', self.TEST_DATA_SOURCE, 'generated', 'embedding_present'
        )
        path_embedding_image: str = join(path_generated_folder, 'embedding.png')
        path_dimensions: str = join(path_generated_folder, 'dimensions.json')
        set_config(self.CUSTOM_CONFIG_PATH_EMBEDDING_PRESENT)

        # execute
        result: str = create_embedding_image(self.TEST_DATA_SOURCE, overlay_type)

        # verify
        assert result
        assert isfile(path_embedding_image)
        assert isfile(path_dimensions)
        assert 'Created embedding image successfully' in caplog.text

        # cleanup
        remove(path_embedding_image)
        remove(path_dimensions)

    def test_valid_create_embedding_image(self, caplog):
        caplog.set_level(logging.INFO)

        # setup
        path_generated_folder: str = join(
            RESOURCES_PATH, 'dim_reduction', self.TEST_DATA_SOURCE, 'generated', 'embedding_present'
        )
        path_image: str = join(path_generated_folder, 'image_index_to_embedding.png')

        # execute
        result: str = get_image_of_indices_to_embedding(self.TEST_DATA_SOURCE)

        # verify
        assert result
        assert isfile(path_image)
        assert 'Created DR image index to embedding.' in caplog.text

        # cleanup
        remove(path_image)
