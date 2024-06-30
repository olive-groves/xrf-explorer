import logging

from os import remove
from os.path import isfile, join, normpath

from xrf_explorer.server.file_system.helper import set_config
from xrf_explorer.server.dim_reduction import (
    generate_embedding, create_embedding_image, get_image_of_indices_to_embedding
)
from xrf_explorer.server.dim_reduction.general import create_image_of_indices_to_embedding

RESOURCES_PATH: str = join('tests', 'resources')


class TestDimReduction:
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, 'configs', 'dim-reduction.yml')
    CUSTOM_CONFIG_PATH_NO_EMBEDDING: str = join(RESOURCES_PATH, 'configs', 'dim-reduction-no-embedding.yml')
    CUSTOM_CONFIG_PATH_EMBEDDING_PRESENT: str = join(RESOURCES_PATH, 'configs', 'dim-reduction-embedding-present.yml')
    TEST_DATA_SOURCE: str = 'test_data_source'
    NO_CUBE_DATA_SOURCE: str = 'no_cube_data_source'
    PATH_TEST_CUBE: str = join(RESOURCES_PATH, 'dim_reduction', TEST_DATA_SOURCE, 'test_cube.dms')
    PATH_GENERATED_FOLDER: str = join(
        RESOURCES_PATH, 'dim_reduction', TEST_DATA_SOURCE, 'generated', 'from_dim_reduction'
    )

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

    def test_no_cube_for_embedding(self, caplog):
        # setup
        element: int = 2
        threshold: int = 0
        umap_args: dict[str, str] = {'n-neighbors': '2', 'metric': 'euclidean'}
        set_config(self.CUSTOM_CONFIG_PATH)

        # execute
        result: str = generate_embedding(self.NO_CUBE_DATA_SOURCE, element, threshold, new_umap_parameters=umap_args)

        # verify
        assert result == 'error'

        # verify log messages
        assert f"Could not get path to elemental datacube of data source {self.NO_CUBE_DATA_SOURCE}" in caplog.text

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

    def do_test_embedding(self, caplog, threshold: int = 100, expected_result: str = 'success'):
        caplog.set_level(logging.INFO)

        # setup
        element: int = 2
        umap_args: dict[str, str] = {'n-neighbors': '2', 'metric': 'euclidean'}
        path_generated = join(
            RESOURCES_PATH, 'dim_reduction', self.TEST_DATA_SOURCE, 'generated', 'from_dim_reduction'
        )
        path_embedding: str = join(path_generated, 'embedded_data.npy')
        path_indices: str = join(path_generated, 'indices.npy')
        path_all_indices: str = join(path_generated, 'all_indices.npy')
        path_mapping_image: str = join(path_generated, 'image_index_to_embedding.png')
        set_config(self.CUSTOM_CONFIG_PATH)

        # execute
        result: str = generate_embedding(self.TEST_DATA_SOURCE, element, threshold, new_umap_parameters=umap_args)

        # verify
        assert result == expected_result
        assert isfile(path_embedding)
        assert isfile(path_indices)
        assert isfile(path_all_indices)
        assert isfile(path_mapping_image)
        assert 'Generated embedding successfully' in caplog.text

        # cleanup
        remove(path_embedding)
        remove(path_indices)
        remove(path_all_indices)
        remove(path_mapping_image)

    def test_valid_embedding(self, caplog):
        self.do_test_embedding(caplog)

    def test_valid_embedding_downsampled(self, caplog):
        self.do_test_embedding(caplog, threshold=0, expected_result='downsampled')

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

    def do_test_valid_image(self, caplog, overlay_type: str):
        caplog.set_level(logging.INFO)

        # setup
        path_generated_folder: str = join(
            RESOURCES_PATH, 'dim_reduction', self.TEST_DATA_SOURCE, 'generated', 'embedding_present'
        )
        path_embedding_image: str = join(path_generated_folder, 'embedding.png')
        set_config(self.CUSTOM_CONFIG_PATH_EMBEDDING_PRESENT)

        # execute
        result: str = create_embedding_image(self.TEST_DATA_SOURCE, overlay_type)

        # verify
        assert result
        assert isfile(path_embedding_image)
        assert 'Created embedding image successfully' in caplog.text

        # cleanup
        remove(path_embedding_image)

    def test_valid_elemental_image(self, caplog):
        self.do_test_valid_image(caplog, 'elemental_1')

    def test_valid_contextual_image(self, caplog):
        self.do_test_valid_image(caplog, 'contextual_RGB')

    def do_test_invalid_embedding_image(
            self, caplog, overlay_type: str,
            expected_caplog: str = "", folder_name: str = 'embedding_present',
            config: str = CUSTOM_CONFIG_PATH_EMBEDDING_PRESENT
    ):
        # setup
        path_generated_folder: str = join(
            RESOURCES_PATH, 'dim_reduction', self.TEST_DATA_SOURCE, 'generated', folder_name
        )
        path_embedding_image: str = join(path_generated_folder, 'embedding.png')
        set_config(config)

        # execute
        result: str = create_embedding_image(self.TEST_DATA_SOURCE, overlay_type)

        # verify
        assert not result
        assert not isfile(path_embedding_image)
        assert expected_caplog in caplog.text

    def test_invalid_element_creating_image(self, caplog):
        self.do_test_invalid_embedding_image(caplog, 'elemental_1000000', expected_caplog='Invalid element: 1000000')

    def test_no_embedding(self, caplog):
        self.do_test_invalid_embedding_image(
            caplog, 'elemental_1',
            expected_caplog='Failed to load indices and/or embedding data.',
            config=self.CUSTOM_CONFIG_PATH_NO_EMBEDDING,
            folder_name='no_embedding'
        )

    def test_invalid_image_type(self, caplog):
        self.do_test_invalid_embedding_image(caplog, 'invalid', expected_caplog='Invalid overlay type: invalid')

    def test_invalid_getting_image_of_indices_invalid_data_source(self, caplog):
        # setup
        set_config(self.CUSTOM_CONFIG_PATH_EMBEDDING_PRESENT)

        # execute
        path: str = get_image_of_indices_to_embedding("non_existent_data_source")
        
        # verify
        assert not path
    
    def test_invalid_getting_image_of_indices_no_image(self, caplog):
        # setup
        set_config(self.CUSTOM_CONFIG_PATH_EMBEDDING_PRESENT)

        # execute
        path: str = get_image_of_indices_to_embedding(self.TEST_DATA_SOURCE)

        # verify
        assert not path
        assert 'File image_index_to_embedding.png not found.' in caplog.text

    def test_valid_create_embedding_image(self, caplog):
        caplog.set_level(logging.INFO)

        # setup
        path_generated_folder: str = join(
            RESOURCES_PATH, 'dim_reduction', self.TEST_DATA_SOURCE, 'generated', 'embedding_present'
        )
        path_image: str = join(path_generated_folder, 'image_index_to_embedding.png')

        # execute
        result: bool = create_image_of_indices_to_embedding(self.TEST_DATA_SOURCE)
        path: str = get_image_of_indices_to_embedding(self.TEST_DATA_SOURCE)

        # verify
        assert result
        assert isfile(path_image)

        assert normpath(path) == normpath(path_image)
        assert 'Created DR image index to embedding.' in caplog.text

        # cleanup
        remove(path_image)
