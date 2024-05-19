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
        args_generating: dict[str, str] = {"element": '9'}
        args_creating: dict[str, str] = {"type": 'rgb'}

        # execute
        result1: bool = generate_embedding(args_generating, 'this-config-does-not-exist.yml')
        result2: bool = create_embedding_image(args_creating, 'this-config-does-not-exist.yml')

        # verify
        assert not result1
        assert not result2

    def test_invalid_element_generating(self, caplog):
        # setup
        args1: dict[str, str] = {"element": '-1'}
        args2: dict[str, str] = {"element": '1000000'}

        # execute
        result1: bool = generate_embedding(args1, self.CUSTOM_CONFIG_PATH)
        result2: bool = generate_embedding(args2, self.CUSTOM_CONFIG_PATH)

        # verify
        assert not result1
        assert not result2
    
    def test_invalid_element_creating_image(self, caplog):
        # setup
        args1: dict[str, str] = {"type": '-1'}
        args2: dict[str, str] = {"type": '1000000'}

        # execute
        result1: bool = create_embedding_image(args1, self.CUSTOM_CONFIG_PATH)
        result2: bool = create_embedding_image(args2, self.CUSTOM_CONFIG_PATH)

        # verify
        assert not result1
        assert not result2

    def test_invalid_umap(self, caplog):
        # setup
        args: dict[str, str] = {"element": '2', "n-neighbors": '0', "min-dist": '0', "n-components": '0', "metric": "invalid"}

        # execute
        result: bool = generate_embedding(args, self.CUSTOM_CONFIG_PATH)

        # verify
        assert not result

    def test_no_embedding(self, caplog):
        # setup
        args: dict[str, str] = {"type": '1'}
        os.remove(join(self.TEMP_FOLDER, 'embedded_data.npy'))
        os.remove(join(self.TEMP_FOLDER, 'indices.npy'))
        
        # execute
        result: bool = create_embedding_image(args, self.CUSTOM_CONFIG_PATH)

        # verify
        assert not result

    def test_valid_embedding(self, caplog):
        # setup
        args: dict[str, str] = {"element": '2', "threshold": '0', "n-neighbors": '2', "metric": "euclidean"}

        # execute
        result: bool = generate_embedding(args, self.CUSTOM_CONFIG_PATH)

        # verify
        assert result
    
    def test_high_threshold(self, caplog):
        # setup
        args: dict[str, str] = {"element": '2', "threshold": '1000', "n-neighbors": '2', "metric": "euclidean"}

        # execute
        result: bool = generate_embedding(args, self.CUSTOM_CONFIG_PATH)

        # verify
        assert not result
    
    def test_valid_image(self, caplog):
        # setup
        args: dict[str, str] = {"type": '1'}

        # execute
        result: bool = create_embedding_image(args, self.CUSTOM_CONFIG_PATH)

        # verify
        assert result
