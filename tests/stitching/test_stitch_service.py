import os
from typing import Any

import pytest
import numpy as np
import cv2
from unittest.mock import patch, MagicMock, mock_open, call

from xrf_explorer.server.stitcher.cube_fragments import SpectralDatacubeFragment
from xrf_explorer.server.stitcher.helper import Dimensions
from xrf_explorer.server.stitcher.stitcher_service import (
    FragmentData,
    StitchData,
    _build_path,
    get_greyscale_path,
    get_stitch_info,
    create_recipe_file,
    generate_partial_greyscale,
    generate_all_partial_greyscales,
    load_greyscale_from_file,
    get_fragment_greyscales,
    stitch,
    stitch_greyscales,
    perform_stitching,
    _transpose_cube_worker,
    pre_transpose_cubes,
    get_transpose_status,
)
from xrf_explorer.server.stitcher.transpose_state import (
    TransposeStateManager,
    TransposeInfo,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_config():
    with patch("xrf_explorer.server.stitcher.stitcher_service.get_config") as mock:
        mock.return_value = {"uploads-folder": "/tmp/uploads"}
        yield mock


@pytest.fixture
def sample_fragment_data_dict():
    return {
        "datacube_file": "test.raw",
        "rpl_file": "test.rpl",
        "rotation": 0,
        "local_points": {
            "top_left": [0, 0],
            "top_right": [10, 0],
            "bottom_left": [0, 10],
            "bottom_right": [10, 10],
        },
        "target_points": {
            "top_left": [5, 5],
            "top_right": [15, 5],
            "bottom_left": [5, 15],
            "bottom_right": [15, 15],
        },
    }


@pytest.fixture
def sample_stitch_json(sample_fragment_data_dict):
    return {
        "type": "spectral",
        "preview": True,
        "contextual_image": "context.png",
        "down_scaling": 0.5,
        "intensity_scales": [1.0],
        "fragments": [sample_fragment_data_dict],
    }


@pytest.fixture
def mock_target_dimensions():
    return Dimensions(100, 100)


# =============================================================================
# Test FragmentData
# =============================================================================


class TestFragmentData:
    @patch("xrf_explorer.server.stitcher.stitcher_service._build_path")
    @patch("xrf_explorer.server.stitcher.stitcher_service.SpectralDatacubeFragment")
    def test_init_spectral_valid(
        self,
        MockSpectral,
        mock_build,
        sample_fragment_data_dict,
        mock_target_dimensions,
    ):
        """Test successful initialization of spectral fragment data."""
        mock_build.side_effect = lambda p, ds: f"/full/{ds}/{p}"
        mock_frag = MagicMock()
        mock_frag.rotated_width = 20
        mock_frag.rotated_height = 20
        MockSpectral.from_file.return_value = mock_frag

        fd = FragmentData(
            sample_fragment_data_dict, "source1", "spectral", mock_target_dimensions
        )

        assert fd.data_source == "source1"
        assert fd.cube_type == "spectral"
        assert fd.datacube_filename == "test.raw"
        assert fd.datacube_path == "/full/source1/test.raw"
        assert fd.rpl_file == "/full/source1/test.rpl"
        assert fd.fragment == mock_frag
        assert fd.rotation == 0
        assert fd.local_points is not None
        assert fd.target_points is not None
        assert fd.points == (fd.local_points, fd.target_points)

    @patch("xrf_explorer.server.stitcher.stitcher_service._build_path")
    @patch("xrf_explorer.server.stitcher.stitcher_service.ElementalDatacubeFragment")
    def test_init_elemental_valid(
        self,
        MockElemental,
        mock_build,
        sample_fragment_data_dict,
        mock_target_dimensions,
    ):
        """Test successful initialization of elemental fragment data."""
        data = sample_fragment_data_dict.copy()
        del data["rpl_file"]  # Elemental doesn't need RPL

        mock_frag = MagicMock()
        mock_frag.rotated_width = 20
        mock_frag.rotated_height = 20
        MockElemental.from_file.return_value = mock_frag

        fd = FragmentData(data, "source1", "elemental", mock_target_dimensions)

        assert fd.cube_type == "elemental"
        with pytest.raises(ValueError, match="'rpl_file' requested but not present"):
            _ = fd.rpl_file

    def test_invalid_filenames(self, mock_target_dimensions):
        """Test validation of filename types."""
        # Spectral missing rpl
        data = {"datacube_file": "test.raw"}  # missing rpl
        with pytest.raises(ValueError, match="must be string"):
            FragmentData(data, "src", "spectral", mock_target_dimensions)

        # Elemental bad type
        data = {"datacube_file": 123}
        with pytest.raises(ValueError, match="must be string"):
            FragmentData(data, "src", "elemental", mock_target_dimensions)

    @patch("xrf_explorer.server.stitcher.stitcher_service._build_path")
    @patch("xrf_explorer.server.stitcher.stitcher_service.ElementalDatacubeFragment")
    def test_invalid_rotation(self, MockFrag, mock_build, mock_target_dimensions):
        """Test validation of rotation values."""
        data = {"datacube_file": "t.dms", "rotation": 45}
        with pytest.raises(ValueError, match="rotation must be one of: 0,90,180,270"):
            FragmentData(data, "src", "elemental", mock_target_dimensions)

    @patch("xrf_explorer.server.stitcher.stitcher_service._build_path")
    @patch("xrf_explorer.server.stitcher.stitcher_service.ElementalDatacubeFragment")
    def test_points_structure_validation(
        self, MockFrag, mock_build, mock_target_dimensions
    ):
        """Test structural validation of points dictionary."""
        base_data: dict[str, Any] = {"datacube_file": "t.dms", "rotation": 0}

        # Test non-dict points
        data = base_data.copy()
        data["local_points"] = "not_a_dict"
        with pytest.raises(ValueError, match="must be dictionary"):
            FragmentData(data, "src", "elemental", mock_target_dimensions)

        # Test bad corner structure
        data = base_data.copy()
        data["local_points"] = {"top_left": "not_list"}
        with pytest.raises(ValueError, match="must be \[x,y\] array"):
            FragmentData(data, "src", "elemental", mock_target_dimensions)

        # Test bad coordinate types
        data = base_data.copy()
        data["local_points"] = {"top_left": ["a", "b"]}
        with pytest.raises(ValueError, match="must be \[x, y\] with integers"):
            FragmentData(data, "src", "elemental", mock_target_dimensions)

        # Test missing points (valid case -> sets to None)
        data = base_data.copy()
        fd = FragmentData(data, "src", "elemental", mock_target_dimensions)
        with pytest.raises(ValueError, match="requested but not present"):
            _ = fd.local_points
        with pytest.raises(ValueError, match="requested but not present"):
            _ = fd.target_points
        with pytest.raises(ValueError, match="requested but not present"):
            _ = fd.points

    @patch("xrf_explorer.server.stitcher.stitcher_service._build_path")
    @patch("xrf_explorer.server.stitcher.stitcher_service.ElementalDatacubeFragment")
    def test_points_bounds_validation(
        self, MockFrag, mock_build, sample_fragment_data_dict, mock_target_dimensions
    ):
        """Test validation of points against dimensions."""
        mock_frag = MagicMock()
        # Make fragment very small so points are out of bounds
        mock_frag.rotated_width = 5
        mock_frag.rotated_height = 5
        MockFrag.from_file.return_value = mock_frag

        # Local points out of bounds
        with pytest.raises(ValueError, match="Fragment local points are out of bounds"):
            FragmentData(
                sample_fragment_data_dict, "src", "elemental", mock_target_dimensions
            )

        # Reset fragment size
        mock_frag.rotated_width = 100
        mock_frag.rotated_height = 100

        # Target points out of bounds
        small_target = Dimensions(5, 5)
        with pytest.raises(
            ValueError, match="Fragment target points are out of bounds"
        ):
            FragmentData(sample_fragment_data_dict, "src", "elemental", small_target)

    def test_property_missing_rotation(self, mock_target_dimensions):
        fd = FragmentData.__new__(FragmentData)
        fd._rotation = None
        with pytest.raises(ValueError, match="rotation' requested but not present"):
            _ = fd.rotation

    def test_property_missing_fragment(self):
        fd = FragmentData.__new__(FragmentData)
        fd._fragment = None
        with pytest.raises(ValueError, match="'fragment' requested but not present"):
            _ = fd.fragment


# =============================================================================
# Test StitchData
# =============================================================================


class TestStitchData:
    @patch("xrf_explorer.server.stitcher.stitcher_service.cv.imread")
    @patch("xrf_explorer.server.stitcher.stitcher_service._build_path")
    @patch("xrf_explorer.server.stitcher.stitcher_service.FragmentData")
    def test_init_valid(
        self, MockFragmentData, mock_build, mock_imread, sample_stitch_json
    ):
        """Test valid initialization of StitchData."""
        # Setup context image mock
        mock_img = np.zeros((100, 200), dtype=np.uint8)  # H=100, W=200
        mock_imread.return_value = mock_img

        # Setup FragmentData mock
        mock_frag_instance = MagicMock()
        mock_frag_instance.fragment = "mock_frag_obj"
        mock_frag_instance.points = ("local", "target")
        MockFragmentData.return_value = mock_frag_instance

        sd = StitchData(sample_stitch_json, "source1")

        assert sd.data_source == "source1"
        assert sd.cube_type == "spectral"
        assert sd.preview is True
        assert sd.contextual_image_dimensions.width == 200
        assert sd.contextual_image_dimensions.height == 100
        assert sd.scaling == 0.5
        assert len(sd.fragment_data) == 1
        assert sd.points == [("local", "target")]
        assert sd.get_fragments() == ["mock_frag_obj"]

    def test_init_missing_data(self):
        with pytest.raises(ValueError, match="Invalid or missing JSON"):
            StitchData(None, "src")

    def test_invalid_type(self, sample_stitch_json):
        data = sample_stitch_json.copy()
        data["type"] = "invalid"
        with pytest.raises(ValueError, match="type must be 'elemental' or 'spectral'"):
            StitchData(data, "src")

    def test_invalid_preview(self, sample_stitch_json):
        data = sample_stitch_json.copy()
        data["preview"] = "not_bool"
        with pytest.raises(ValueError, match="preview must be boolean"):
            StitchData(data, "src")

    def test_invalid_contextual_image_name(self, sample_stitch_json):
        data = sample_stitch_json.copy()
        data["contextual_image"] = 123
        with pytest.raises(ValueError, match="contextual_image must be string"):
            StitchData(data, "src")

    @patch(
        "xrf_explorer.server.stitcher.stitcher_service.StitchData.init_contextual_image_dimensions",
        return_value=None,
    )
    def test_invalid_scaling(self, mock_init_dims, sample_stitch_json):
        data = sample_stitch_json.copy()
        data["down_scaling"] = "NaN"
        with pytest.raises(ValueError, match="down_scaling must be a number"):
            StitchData(data, "src")

        data["down_scaling"] = -1
        with pytest.raises(ValueError, match="down_scaling must be a number"):
            StitchData(data, "src")

    @patch(
        "xrf_explorer.server.stitcher.stitcher_service.StitchData.init_contextual_image_dimensions",
        return_value=None,
    )
    def test_invalid_fragments_list(self, mock_init_dims, sample_stitch_json):
        data = sample_stitch_json.copy()
        data["fragments"] = []
        with pytest.raises(ValueError, match="fragments must be a non-empty list"):
            StitchData(data, "src")

        data["fragments"] = ["not_dict"]
        with pytest.raises(ValueError, match="must be an object"):
            StitchData(data, "src")

    @patch("xrf_explorer.server.stitcher.stitcher_service.cv.imread")
    @patch("xrf_explorer.server.stitcher.stitcher_service._build_path")
    @patch("xrf_explorer.server.stitcher.stitcher_service.FragmentData")
    def test_intensity_scales_validation(
        self, MockFD, mock_build, mock_imread, sample_stitch_json
    ):
        """Test intensity scales validation when is_stitching=True."""
        mock_imread.return_value = np.zeros((10, 10))

        # Valid case
        sd = StitchData(sample_stitch_json, "src", is_stitching=True)
        assert sd._intensity_scales == [1.0]

        # Missing scales
        data = sample_stitch_json.copy()
        del data["intensity_scales"]
        with pytest.raises(ValueError, match="must be a non-empty float list"):
            StitchData(data, "src", is_stitching=True)

        # Invalid types in list
        data = sample_stitch_json.copy()
        data["intensity_scales"] = [True]  # bool check
        with pytest.raises(ValueError, match="must contain only numbers"):
            StitchData(data, "src", is_stitching=True)

        data["intensity_scales"] = ["string"]
        with pytest.raises(ValueError, match="must contain only numbers"):
            StitchData(data, "src", is_stitching=True)

    @patch("xrf_explorer.server.stitcher.stitcher_service.cv.imread")
    @patch("xrf_explorer.server.stitcher.stitcher_service._build_path")
    def test_contextual_image_errors(self, mock_build, mock_imread, sample_stitch_json):
        # File not found (imread returns None)
        mock_imread.return_value = None
        with pytest.raises(FileNotFoundError, match="Failed to load contextual image"):
            StitchData(sample_stitch_json, "src")

        # Invalid dims (0 width)
        mock_imread.return_value = np.zeros((0, 10))
        with pytest.raises(ValueError, match="Contextual image has invalid dimensions"):
            StitchData(sample_stitch_json, "src")

        # No contextual image provided logic
        data = sample_stitch_json.copy()
        data["contextual_image"] = None
        # Mocking fragment data to skip validation inside it requiring dims
        with patch("xrf_explorer.server.stitcher.stitcher_service.FragmentData"):
            sd = StitchData(data, "src")
            assert sd._contextual_image_dimensions is None
            with pytest.raises(ValueError, match="contextual image not present"):
                _ = sd.contextual_image_dimensions

    def test_property_missing_attributes(self):
        sd = StitchData.__new__(StitchData)
        sd._points = None
        sd._scaling = None
        sd._preview = None

        with pytest.raises(ValueError, match="no points present"):
            _ = sd.points
        with pytest.raises(ValueError, match="down_scale not in request"):
            _ = sd.scaling
        with pytest.raises(ValueError, match="not in request"):
            _ = sd.preview

    @patch("xrf_explorer.server.stitcher.stitcher_service.ScalarOptimizer")
    @patch("xrf_explorer.server.stitcher.stitcher_service.DatacubeStitcher")
    def test_get_datacube_stitcher(self, MockStitcher, MockOptimizer):
        # Setup StitchData manually to avoid __init__ overhead for this test
        sd = StitchData.__new__(StitchData)
        sd.data_source = "src"
        sd.fragment_data = []
        sd._points = []
        sd._scaling = 0.5
        sd._intensity_scales = [1.0]
        sd._contextual_image_dimensions = Dimensions(100, 100)

        # Mock get_fragments
        sd.get_fragments = MagicMock(return_value=[])

        # Mock Optimizer behavior
        mock_opt_instance = MockOptimizer.return_value
        mock_opt_instance.find_best_scalar.return_value = (
            2.0,
            0.1,
        )  # optimal scalar, cost

        # Call
        with patch(
            "xrf_explorer.server.stitcher.stitcher_service._build_path",
            return_value="/out",
        ):
            result = sd.get_datacube_stitcher()

        # Assert
        assert result == MockStitcher.return_value
        # Check if scalar was multiplied (2.0 * 0.5 = 1.0)
        args, kwargs = MockStitcher.call_args
        # signature: fragments, intensity_scales, points, dim, scalar, out_dir, source
        assert args[4] == 1.0

    # =============================================================================


# Test Helper Functions
# =============================================================================


class TestHelpers:
    def test_build_path_no_config(self):
        with patch(
            "xrf_explorer.server.stitcher.stitcher_service.get_config", return_value=None
        ):
            with pytest.raises(ValueError, match="Backend configuration is empty"):
                _build_path("file", "src")

    def test_build_path_missing_source(self, mock_config):
        with patch(
            "xrf_explorer.server.stitcher.stitcher_service.exists", return_value=False
        ):
            with pytest.raises(ValueError, match="Data source folder.*does not exist"):
                _build_path("file", "src")

    @patch("xrf_explorer.server.stitcher.stitcher_service.exists", return_value=True)
    def test_build_path_success(self, mock_exists, mock_config):
        path = _build_path("file.txt", "src")
        # Windows/Linux separation agnostic check or use os.path.join
        assert "uploads" in str(path)
        assert "src" in str(path)
        assert "file.txt" in str(path)

    @patch("xrf_explorer.server.stitcher.stitcher_service._build_path")
    @patch("xrf_explorer.server.stitcher.stitcher_service.os.makedirs")
    def test_get_greyscale_path(self, mock_makedirs, mock_build):
        from os.path import join
        # Use join in the mock to handle separators correctly
        mock_build.side_effect = lambda p, ds: join("/root", ds, p)

        result = get_greyscale_path("test.raw", "src")

        # Build the expected string using join
        expected = join("/root", "src", "generated", "stitching", "test.raw.png")

        assert result == expected
        mock_makedirs.assert_called_once()

    @patch("xrf_explorer.server.stitcher.stitcher_service.ScalarOptimizer")
    def test_get_stitch_info(self, MockOptimizer):
        # Mock Data
        mock_data = MagicMock(spec=StitchData)
        mock_data.points = []
        mock_data.contextual_image_dimensions = Dimensions(10, 10)
        mock_fragment = MagicMock()
        mock_fragment.channels = 4
        mock_data.get_fragments.return_value = [mock_fragment]

        # Mock Optimizer
        mock_opt = MockOptimizer.return_value
        mock_opt.find_best_scalar.return_value = (1.5, 0.0)
        mock_opt.calculate_loss_percentage.return_value = [10.0]

        info = get_stitch_info(mock_data)

        assert info["optimal_scalar"] == 1.5
        assert info["losses"] == [10.0]
        # (4 + 1) * 10 * 10 = 500
        assert info["full_size"] == 500

    def test_create_recipe_file(self):
        m = mock_open()
        with patch("builtins.open", m):
            create_recipe_file("recipe.csv", Dimensions(10, 20), Dimensions(100, 200))

        handle = m()
        # Verify header and some content
        handle.write.assert_any_call("Butterfly Registrator\n")
        # Check dimensions writing (from_w-1, to_w-1) -> 9, 99
        handle.write.assert_any_call("9|0|99|0\n")


# =============================================================================
# Test Greyscale Generation
# =============================================================================


class TestGreyscaleGeneration:
    @patch("xrf_explorer.server.stitcher.stitcher_service.cv.imwrite")
    @patch("xrf_explorer.server.stitcher.stitcher_service.get_greyscale_path")
    def test_generate_partial_greyscale_success(self, mock_get_path, mock_imwrite):
        frag_data = MagicMock(spec=FragmentData)
        frag_data.fragment.create_greyscale_projection.return_value = np.zeros((10, 10))
        frag_data.datacube_filename = "test.raw"
        frag_data.data_source = "data_source"

        result = generate_partial_greyscale(frag_data)

        assert result is True
        mock_imwrite.assert_called_once()

    def test_generate_partial_greyscale_exceptions(self):
        frag_data = MagicMock()
        frag_data.fragment.create_greyscale_projection.side_effect = FileNotFoundError(
            "err"
        )
        assert generate_partial_greyscale(frag_data) is False

        frag_data.fragment.create_greyscale_projection.side_effect = ValueError("err")
        assert generate_partial_greyscale(frag_data) is False

        frag_data.fragment.create_greyscale_projection.side_effect = cv2.error("err")
        assert generate_partial_greyscale(frag_data) is False

        frag_data.fragment.create_greyscale_projection.side_effect = Exception("err")
        assert generate_partial_greyscale(frag_data) is False

    @patch("xrf_explorer.server.stitcher.stitcher_service.generate_partial_greyscale")
    @patch("xrf_explorer.server.stitcher.stitcher_service.exists")
    @patch("xrf_explorer.server.stitcher.stitcher_service.get_greyscale_path")
    def test_generate_all_partial_greyscales(self, mock_path, mock_exists, mock_gen):
        data = MagicMock(spec=StitchData)
        f1 = MagicMock()
        data.fragment_data = [f1]

        # Case 1: File does not exist, generation needed
        mock_exists.return_value = False
        mock_gen.return_value = True

        assert generate_all_partial_greyscales(data) is True
        mock_gen.assert_called_with(f1)

    @patch("xrf_explorer.server.stitcher.stitcher_service.cv.imread")
    @patch("xrf_explorer.server.stitcher.stitcher_service.get_greyscale_path")
    def test_load_greyscale_from_file(self, mock_path, mock_imread):
        # Success
        mock_imread.return_value = np.zeros((5, 5))
        img = load_greyscale_from_file("test", "src")
        assert img is not None

        # Fail
        mock_imread.return_value = None
        with pytest.raises(FileNotFoundError):
            load_greyscale_from_file("test", "src")

    @patch("xrf_explorer.server.stitcher.stitcher_service.cv.imread")
    @patch("xrf_explorer.server.stitcher.stitcher_service.generate_partial_greyscale")
    @patch("xrf_explorer.server.stitcher.stitcher_service.exists")
    @patch("xrf_explorer.server.stitcher.stitcher_service.get_greyscale_path")
    def test_get_fragment_greyscales(
        self, mock_path, mock_exists, mock_gen, mock_imread
    ):
        data = MagicMock()
        f1 = MagicMock()
        data.fragment_data = [f1]

        # File exists
        mock_exists.return_value = True
        mock_imread.return_value = "image_data"

        result = get_fragment_greyscales(data)

        assert result == ["image_data"]
        mock_gen.assert_not_called()

        # File doesn't exist
        mock_exists.return_value = False
        get_fragment_greyscales(data)
        mock_gen.assert_called_once()


# =============================================================================
# Test Stitching Logic
# =============================================================================


class TestStitching:
    @patch("xrf_explorer.server.stitcher.stitcher_service.perform_stitching")
    @patch("xrf_explorer.server.stitcher.stitcher_service.stitch_greyscales")
    def test_stitch_dispatcher(self, mock_preview, mock_full):
        data = MagicMock(spec=StitchData)

        # Preview
        data.preview = True
        stitch(data)
        mock_preview.assert_called_once_with(data)
        mock_full.assert_not_called()

        # Full
        mock_preview.reset_mock()
        data.preview = False
        stitch(data)
        mock_full.assert_called_once_with(data)
        mock_preview.assert_not_called()

    @patch("xrf_explorer.server.stitcher.stitcher_service.cv.imwrite")
    @patch("xrf_explorer.server.stitcher.stitcher_service.os.makedirs")
    @patch("xrf_explorer.server.stitcher.stitcher_service.create_recipe_file")
    @patch("xrf_explorer.server.stitcher.stitcher_service.normalize_image")
    @patch("xrf_explorer.server.stitcher.stitcher_service.get_fragment_greyscales")
    @patch("xrf_explorer.server.stitcher.stitcher_service._build_path")
    def test_stitch_greyscales(
        self,
        mock_build,
        mock_get_greys,
        mock_norm,
        mock_recipe,
        mock_mkdirs,
        mock_imwrite,
    ):
        # Setup Data
        data = MagicMock(spec=StitchData)
        data.data_source = "src"
        data.contextual_image_dimensions = Dimensions(100, 100)

        # Setup Stitcher
        mock_stitcher = MagicMock()
        mock_stitcher.stitch_greyscales.return_value = np.zeros((50, 50))
        mock_stitcher.scaled_width = 50
        mock_stitcher.scaled_height = 50
        data.get_datacube_stitcher.return_value = mock_stitcher

        # Setup Mocks
        mock_get_greys.return_value = ["img1", "img2"]
        mock_norm.return_value = np.zeros((50, 50))  # normalized image
        mock_build.return_value = "/tmp/path"

        result = stitch_greyscales(data)

        assert result["status"] == "success"
        assert result["preview"] is True
        assert result["dimensions"]["width"] == 50
        mock_recipe.assert_called_once()
        mock_imwrite.assert_called_once()

    @patch("xrf_explorer.server.stitcher.stitcher_service.cv.imwrite")
    @patch("xrf_explorer.server.stitcher.stitcher_service.os.makedirs")
    @patch("xrf_explorer.server.stitcher.stitcher_service.create_recipe_file")
    @patch("xrf_explorer.server.stitcher.stitcher_service.normalize_image")
    @patch("xrf_explorer.server.stitcher.stitcher_service._build_path")
    def test_perform_stitching(
        self, mock_build, mock_norm, mock_recipe, mock_mkdirs, mock_imwrite
    ):
        # Setup Data
        data = MagicMock(spec=StitchData)
        data.data_source = "src"
        data.contextual_image_dimensions = Dimensions(100, 100)

        # Setup Stitcher & Result Fragment
        mock_stitcher = MagicMock()
        result_frag = MagicMock()
        result_frag.is_spectral = True
        result_frag.width = 100
        result_frag.height = 100
        result_frag.channels = 10
        result_frag.datacube_file = "result.raw"
        result_frag.create_greyscale_projection.return_value = np.zeros((10, 10))

        mock_stitcher.stitch_datacubes.return_value = result_frag
        data.get_datacube_stitcher.return_value = mock_stitcher

        mock_norm.return_value = np.zeros((10, 10))

        result = perform_stitching(data)

        assert result["status"] == "success"
        assert result["preview"] is False
        assert result["type"] == "spectral"
        assert result["rpl_file"] == "stitched_spectral.rpl"
        mock_recipe.assert_called_once()
        mock_imwrite.assert_called_once()

        # Test Elemental branch
        result_frag.is_spectral = False
        result = perform_stitching(data)
        assert result["type"] == "elemental"
        assert result["rpl_file"] is None


# =============================================================================
# Test Transposition
# =============================================================================


class TestTransposition:
    @patch("xrf_explorer.server.stitcher.stitcher_service.TransposeStateManager")
    def test_transpose_cube_worker(self, MockManager):
        # Success case
        frag = MagicMock()
        frag.create_transposed_version.return_value.datacube_file = "transposed.raw"
        manager = MagicMock()

        _transpose_cube_worker(frag, "src", "cube.raw", manager)

        manager.complete_transpose.assert_called_with(
            "src", "cube.raw", transposed_path="transposed.raw"
        )

        # Error case
        frag.create_transposed_version.side_effect = Exception("Fail")
        _transpose_cube_worker(frag, "src", "cube.raw", manager)

        # Verify call args for error
        args, kwargs = manager.complete_transpose.call_args
        assert kwargs["error"] == "Fail"

    @patch("xrf_explorer.server.stitcher.stitcher_service.SpectralDatacubeFragment")
    @patch("xrf_explorer.server.stitcher.stitcher_service.TransposeStateManager")
    def test_pre_transpose_cubes(self, MockManager, MockSpectral):
        data = MagicMock(spec=StitchData)
        data.data_source = "src"

        f1_data = MagicMock()
        f1_data.datacube_filename = "el.dms"
        f1_frag = MagicMock()
        f1_frag.is_spectral = False
        f1_data.fragment = f1_frag

        f2_data = MagicMock()
        f2_data.datacube_filename = "sp_done.raw"
        f2_frag = MagicMock()
        f2_frag.is_spectral = True
        f2_frag.is_transposed = True
        f2_data.fragment = f2_frag

        f3_data = MagicMock()
        f3_data.datacube_filename = "sp_todo.raw"
        f3_frag = MagicMock()
        f3_frag.is_spectral = True
        f3_frag.is_transposed = False
        f3_data.fragment = f3_frag

        f4_data = MagicMock()
        f4_data.datacube_filename = "sp_busy.raw"
        f4_frag = MagicMock()
        f4_frag.is_spectral = True
        f4_frag.is_transposed = False
        f4_data.fragment = f4_frag

        data.fragment_data = [f1_data, f2_data, f3_data, f4_data]

        mock_instance = MockManager.get_instance.return_value

        def enqueue_side_effect(ds, cf, worker):
            return cf == "sp_todo.raw"

        mock_instance.enqueue_transpose.side_effect = enqueue_side_effect

        mock_status = MagicMock()
        mock_status.status.value = "in_progress"
        mock_instance.get_status.return_value = mock_status

        result = pre_transpose_cubes(data)

        assert result["status"] == "queued"
        assert len(result["cubes_queued"]) == 1
        assert result["cubes_queued"][0]["cube_file"] == "sp_todo.raw"
        assert len(result["cubes_skipped"]) == 3

        skipped_files = {x["cube_file"]: x["reason"] for x in result["cubes_skipped"]}
        assert "sp_busy.raw" in skipped_files
        assert "already in_progress" in skipped_files["sp_busy.raw"]

    @patch("xrf_explorer.server.stitcher.stitcher_service.TransposeStateManager")
    def test_get_transpose_status(self, MockManager):
        mock_instance = MockManager.get_instance.return_value

        # Mock statuses
        info = MagicMock(spec=TransposeInfo)
        info.to_dict.return_value = {"status": "done"}

        mock_instance.get_all_statuses.return_value = {"test.raw": info}
        mock_instance.is_any_in_progress.return_value = False

        result = get_transpose_status("src")

        assert result["data_source"] == "src"
        assert result["any_in_progress"] is False
        assert result["cubes"]["test.raw"]["status"] == "done"