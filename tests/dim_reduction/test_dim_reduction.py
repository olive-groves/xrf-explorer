import sys
import os

from os.path import join
from pathlib import Path

sys.path.append('.')

from xrf_explorer.server.dim_reduction.embedding import generate_embedding
from xrf_explorer.server.dim_reduction.overlay import create_embedding_image

RESOURCES_PATH: Path = Path('tests', 'resources')


class TestDimReduction:
    CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, Path('configs', 'dim-reduction.yml'))
    TEMP_FOLDER: str = join(RESOURCES_PATH, 'dim_reduction', 'dim_reduction')

    def test_config_not_found(self, caplog):
        # setup
        element: int = 9
        threshold: int = 100
        overlay_type: str = 'rgb'

        # execute
        result1: bool = generate_embedding(element, threshold, config_path='this-config-does-not-exist.yml')
        result2: bool = create_embedding_image(overlay_type, config_path='this-config-does-not-exist.yml')

        # verify
        assert not result1
        assert not result2

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
    
    def test_invalid_element_creating_image(self, caplog):
        # setup
        overlay_type1: str = '-1'
        overlay_type2: str = '1000000'

        # execute
        result1: bool = create_embedding_image(overlay_type1, config_path=self.CUSTOM_CONFIG_PATH)
        result2: bool = create_embedding_image(overlay_type2, config_path=self.CUSTOM_CONFIG_PATH)

        # verify
        assert not result1
        assert not result2

    def test_invalid_umap(self, caplog):
        # setup
        element: int = 2
        threshold: int = 100
        umap_args: dict[str, str] = {"n-neighbors": '0', "min-dist": '0', "n-components": '0', "metric": "invalid"}

        # execute
        result: bool = generate_embedding(element, threshold, umap_parameters=umap_args, config_path=self.CUSTOM_CONFIG_PATH)

        # verify
        assert not result

    def test_no_embedding(self, caplog):
        # setup
        overlay_type: str = '1'
        os.remove(join(self.TEMP_FOLDER, 'embedded_data.npy'))
        os.remove(join(self.TEMP_FOLDER, 'indices.npy'))
        
        # execute
        result: bool = create_embedding_image(overlay_type, config_path=self.CUSTOM_CONFIG_PATH)

        # verify
        assert not result

    def test_valid_embedding(self, caplog):
        # setup
        element: int = 2
        threshold: int = 0
        umap_args: dict[str, str] = {"n-neighbors": '2', "metric": "euclidean"}

        # execute
        result: bool = generate_embedding(element, threshold, umap_parameters=umap_args, config_path=self.CUSTOM_CONFIG_PATH)

        # verify
        assert result
    
    def test_high_threshold(self, caplog):
        # setup
        element: int = 2
        threshold: int = 1000
        umap_args: dict[str, str] = {"n-neighbors": '2', "metric": "euclidean"}

        # execute
        result: bool = generate_embedding(element, threshold, umap_parameters=umap_args, config_path=self.CUSTOM_CONFIG_PATH)

        # verify
        assert not result
    
    def test_valid_image(self, caplog):
        # setup
        overlay_type: str = '1'

        # execute
        result: bool = create_embedding_image(overlay_type, config_path=self.CUSTOM_CONFIG_PATH)

        # verify
        assert result
