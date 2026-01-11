import logging
import os
import sys

import cv2
import numpy as np
import pytest
from os.path import join
from unittest.mock import patch, MagicMock

from xrf_explorer.server.stitcher.helper import (
    WarpSelection,
    Dimensions,
    ScalarOptimizer,
    split_range,
    transpose_spectral_datacube,
    rotate_cv,
    normalize_image,
    TransposeMode,
)

from xrf_explorer.server.stitcher.cube_fragments import (
    DatacubeFragment,
    ElementalDatacubeFragment,
    SpectralDatacubeFragment,
)

RESOURCES_PATH: str = join("tests", "resources")

DATA_SOURCE = "data_source"


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_warp_selection():
    """Create a sample WarpSelection for testing."""
    return WarpSelection(
        top_left=(0, 100),
        top_right=(30, 100),
        bottom_left=(0, 70),
        bottom_right=(30, 70),
        total_height=100,
    )


@pytest.fixture
def sample_warp_selection_2():
    """Create a second sample WarpSelection for optimizer testing."""
    return WarpSelection(
        top_left=(0, 100),
        top_right=(60, 100),
        bottom_left=(0, 40),
        bottom_right=(60, 40),
        total_height=100,
    )


@pytest.fixture
def sample_optimizer(sample_warp_selection, sample_warp_selection_2):
    """Create a ScalarOptimizer with test data."""
    return ScalarOptimizer([(sample_warp_selection, sample_warp_selection_2)])

@pytest.fixture
def sample_test_image():
    """Load test image from resources."""
    import cv2

    img_path = join(RESOURCES_PATH, "stitching", "data_source", "test_image_stitching.png")
    print(img_path)
    return cv2.imread(img_path)

@pytest.fixture
def sample_rpl_file(tmp_path):
    """Create a sample RPL metadata file."""
    rpl_path = tmp_path / "test.rpl"
    rpl_content = """key       	value
width       	10
height      	8
depth       	4
offset      	0
data-Length 	2
data-type   	unsigned
byte-order  	little-endian
"""
    rpl_path.write_text(rpl_content)
    return rpl_path

@pytest.fixture
def sample_spectral_file(tmp_path, sample_rpl_file):
    """Create a sample spectral datacube file with RPL."""
    raw_path = tmp_path / "test.raw"
    data = np.arange(10 * 8 * 4, dtype=np.uint16).reshape((8, 10, 4))
    data.tofile(str(raw_path))
    return raw_path, sample_rpl_file, data

# =============================================================================
# Test Classes
# =============================================================================


class TestDimensions:
    """Tests for Dimensions class."""

    def test_init_basic(self):
        """Test basic initialization."""
        dims = Dimensions(width=100, height=200)
        assert dims.width == 100
        assert dims.height == 200


class TestWarpSelection:
    """Tests for WarpSelection class."""

    def test_init_coordinates_transformation(self, sample_warp_selection):
        """Test that Y coordinates are correctly transformed."""
        selection = sample_warp_selection

        # Assert - Y coordinates should be inverted
        assert selection.top_left == (0, 0)
        assert selection.top_right == (30, 0)
        assert selection.bottom_left == (0, 30)
        assert selection.bottom_right == (30, 30)

    def test_get_points_default_scalar(self, sample_warp_selection):
        """Test get_points with default scalar 1.0."""
        points = sample_warp_selection.get_points()

        assert points.dtype == np.float32
        assert points.shape == (4, 2)
        np.testing.assert_array_equal(points[0], [0, 0])
        np.testing.assert_array_equal(points[1], [30, 0])
        np.testing.assert_array_equal(points[2], [0, 30])
        np.testing.assert_array_equal(points[3], [30, 30])

    def test_get_points_scalar_2(self ,sample_warp_selection):
        """Test get_points with scalar 2.0."""
        points = sample_warp_selection.get_points(scalar=2.0)

        assert points.dtype == np.float32
        assert points.shape == (4, 2)
        np.testing.assert_array_equal(points[0], [0, 0])
        np.testing.assert_array_equal(points[1], [60, 0])
        np.testing.assert_array_equal(points[2], [0, 60])
        np.testing.assert_array_equal(points[3], [60, 60])

    def test_get_points_scalar_half(self, sample_warp_selection):
        """Test get_points with scalar 0.5."""
        points = sample_warp_selection.get_points(scalar=0.5)

        assert points.dtype == np.float32
        assert points.shape == (4, 2)
        np.testing.assert_array_equal(points[0], [0, 0])
        np.testing.assert_array_equal(points[1], [15, 0])
        np.testing.assert_array_equal(points[2], [0, 15])
        np.testing.assert_array_equal(points[3], [15, 15])

    def test_are_within_all_inside(self, sample_warp_selection):
        """Test are_within when all points are inside bounds."""
        assert sample_warp_selection.are_within(width=150, height=150) is True

    def test_are_within_one_out(self):
        """Test are_within when one point is outside."""
        selection = WarpSelection(
            top_left=(10, 20),
            top_right=(100, 20),
            bottom_left=(10, 80),
            bottom_right=(200, 80),  # x=200 is outside if width=150
            total_height=100,
        )

        assert selection.are_within(width=150, height=150) is False

    def test_str_representation(self, sample_warp_selection):
        """Test string representation contains expected elements."""

        str_repr = str(sample_warp_selection)

        assert "WarpSelection" in str_repr
        assert "TL:" in str_repr
        assert "TR:" in str_repr
        assert "BL:" in str_repr
        assert "BR:" in str_repr


class TestScalarOptimizer:
    """Tests for ScalarOptimizer class."""

    def test_init_empty_list(self):
        """Test initialization with empty points list."""
        optimizer = ScalarOptimizer([])

        assert optimizer.points == []

    def test_init_with_points(self, sample_optimizer, sample_warp_selection, sample_warp_selection_2):
        """Test initialization with valid points list."""


        assert len(sample_optimizer.points) == 1
        assert sample_optimizer.points[0] == (sample_warp_selection, sample_warp_selection_2)

    def test_calculate_loss_percentage_basic(self, sample_optimizer):
        """Test basic loss percentage calculation."""
        loss = sample_optimizer.calculate_loss_percentage(1.0)

        assert len(loss) == 1
        assert loss[0] == 200.0

    def test_calculate_loss_percentage_different_scalar(self, sample_optimizer):
        """Test loss calculation with different scalar."""
        loss = sample_optimizer.calculate_loss_percentage(2.0)

        assert len(loss) == 1
        # With scalar=2.0, the loss should be different
        assert loss[0] != 100.0

    def test_get_scale_factor_identical_regions(self, sample_optimizer, sample_warp_selection):
        """Test scale factor for identical regions."""
        optimizer = ScalarOptimizer([(sample_warp_selection, sample_warp_selection)])
        scale = optimizer.get_scale_factor(sample_warp_selection, sample_warp_selection, 1.0)

        assert 0.999 < scale < 1.001

    @patch("xrf_explorer.server.stitcher.helper.cv.findHomography")
    def test_get_scale_factor_scaled_regions(self, mock_find_homography):
        """Test scale factor for scaled regions."""
        # Create a homography that scales by 2x
        scale_2 = np.array(
            [[2, 0, 0], [0, 2, 0], [0, 0, 1]], dtype=np.float64
        )
        mock_find_homography.return_value = (scale_2, None)

        src = WarpSelection((10, 20), (100, 20), (10, 80), (100, 80), 100)
        dst = WarpSelection((10, 20), (100, 20), (10, 80), (100, 80), 100)

        optimizer = ScalarOptimizer([])
        scale = optimizer.get_scale_factor(src, dst, 1.0)

        # For 2x scaling homography, scale should be ~2.0
        assert 1.99 < scale < 2.01

    def test_cost_function_optimal_scalar(self):
        """Test cost function with optimal scalar for matching regions."""
        src = WarpSelection((10, 20), (100, 20), (10, 80), (100, 80), 100)
        dst = WarpSelection((10, 20), (100, 20), (10, 80), (100, 80), 100)

        optimizer = ScalarOptimizer([(src, dst)])
        cost = optimizer.cost_function(1.0)

        # For matching regions with scalar=1.0, cost should be small
        assert isinstance(cost, float)
        assert cost >= 0

    def test_cost_function_suboptimal_scalar(self):
        """Test cost function with suboptimal scalar."""
        src = WarpSelection((10, 20), (100, 20), (10, 80), (100, 80), 100)
        dst = WarpSelection((10, 20), (100, 20), (10, 80), (100, 80), 100)

        optimizer = ScalarOptimizer([(src, dst)])

        cost_optimal = optimizer.cost_function(1.0)
        cost_suboptimal = optimizer.cost_function(2.0)

        # Suboptimal should generally have higher cost
        assert cost_suboptimal >= 0

    def test_cost_function_empty_points(self):
        """Test cost function with empty points list."""
        optimizer = ScalarOptimizer([])

        # Division by zero protection
        with pytest.raises(ZeroDivisionError):
            optimizer.cost_function(1.0)


class TestSplitRange:
    """Tests for split_range function."""

    def test_single_part(self):
        """Test that single part returns full range."""
        result = split_range(0, 100, 1)
        assert result == [(0, 100)]

    def test_even_division(self):
        """Test even division of range."""
        result = split_range(0, 10, 2)
        assert result == [(0, 5), (5, 10)]

    def test_uneven_division(self):
        """Test uneven division of range."""
        result = split_range(0, 10, 3)
        assert result == [(0, 4), (4, 7), (7, 10)]

    def test_zero_parts_raises_error(self):
        """Test that zero parts raises ValueError."""
        with pytest.raises(ValueError, match="parts must be >= 1"):
            split_range(0, 100, 0)

    def test_start_equals_end(self):
        """Test handling of zero-length range."""
        result = split_range(5, 5, 3)
        assert result == [(5, 5), (5, 5), (5, 5)]

    def test_full_coverage(self):
        """Test that all ranges cover [start, end) without gaps."""
        start, end = 0, 100
        parts = 7
        result = split_range(start, end, parts)

        # Check that ranges are contiguous
        for i in range(len(result) - 1):
            assert result[i][1] == result[i + 1][0]

        # Check that first starts at start and last ends at end
        assert result[0][0] == start
        assert result[-1][1] == end

    def test_no_overlaps(self):
        """Test that ranges don't overlap."""
        result = split_range(0, 100, 10)

        for i in range(len(result) - 1):
            # End of one should equal start of next, no overlap
            assert result[i][1] == result[i + 1][0]

class TestTransposeDatacube:
    """Tests for transpose_spectral_datacube function."""

    def test_hwc_to_chw(self, tmp_path, sample_spectral_file):
        """Test HWC to CHW transposition (8x8x4 -> 4x8x8)."""
        input_path, _, input_data = sample_spectral_file
        output_path = tmp_path / "output.raw"

        transpose_spectral_datacube(str(input_path), str(output_path), (8, 10, 4), (4, 8, 10), "uint16", TransposeMode.HWC_TO_CHW)

        output_data = np.fromfile(output_path, dtype="uint16").reshape(4, 8, 10)
        expected = input_data.transpose(2, 0, 1)
        assert np.array_equal(output_data, expected)


    def test_chw_to_hwc(self, tmp_path, sample_spectral_file):
        """Test CHW to HWC transposition (4x8x8 -> 8x8x4)."""
        # Create input data in CHW format
        _,_,org_input_data = sample_spectral_file
        input_data = org_input_data.transpose(2, 0, 1)
        input_path = tmp_path / "input.raw"
        output_path = tmp_path / "output.raw"
        input_data.tofile(str(input_path))

        transpose_spectral_datacube(str(input_path), str(output_path), (4, 8, 10), (8, 10, 4), "uint16", TransposeMode.CHW_TO_HWC)

        output_data = np.fromfile(str(output_path), dtype="uint16").reshape(8, 10, 4)
        expected = org_input_data
        assert np.array_equal(output_data, expected)

    def test_unsupported_transpose_raises_error(self, tmp_path):
        """Test that unsupported transpose raises ValueError."""
        input_data = np.arange(64).reshape(4, 4, 4).astype("uint16")
        input_path = tmp_path / "input.raw"
        output_path = tmp_path / "output.raw"
        input_data.tofile(str(input_path))

        with pytest.raises(ValueError, match="Unsupported transpose"):
            transpose_spectral_datacube(
                str(input_path), str(output_path), (4, 4, 4), (5, 5, 5), "uint16", TransposeMode.HWC_TO_CHW
            )

class TestRotateCv:
    """Tests for rotate_cv function."""

    def test_no_rotation(self):
        """Test that rotation=0 returns original."""
        img = np.arange(9).reshape(3, 3).astype(np.uint8)
        result = rotate_cv(img, 0)
        assert np.array_equal(result, img)

    def test_90_degrees(self):
        """Test 90-degree counter-clockwise rotation."""
        img = np.zeros((3, 3), dtype=np.uint8)
        img[0, 0] = 1
        result = rotate_cv(img, 90)
        assert result[2, 0] == 1

    def test_180_degrees(self):
        """Test 180-degree rotation."""
        img = np.zeros((3, 3), dtype=np.uint8)
        img[0, 0] = 1
        result = rotate_cv(img, 180)
        assert result[2, 2] == 1

    def test_270_degrees(self):
        """Test 270-degree (90 CW) rotation."""
        img = np.zeros((3, 3), dtype=np.uint8)
        img[0, 0] = 1
        result = rotate_cv(img, 270)
        assert result[0, 2] == 1

    def test_invalid_rotation(self):
        """Test that invalid rotation raises ValueError."""
        img = np.zeros((10, 10), dtype=np.uint8)
        with pytest.raises(ValueError, match="Rotation must be"):
            rotate_cv(img, 45)

    def test_with_test_image(self, sample_test_image):
        """Test rotation using actual test image from resources."""
        # Test all valid rotations
        for rot in [0, 90, 180, 270]:
            result = rotate_cv(sample_test_image, rot)
            if rot in [0, 180]:
                assert result.shape[:2] == sample_test_image.shape[:2]
            else:
                assert result.shape[:2] == sample_test_image.shape[:2][::-1]

class TestNormalizeImage:
    """Tests for normalize_image function."""

    def test_normalize_basic(self):
        """Test basic normalization."""
        data = np.array([0, 127, 255], dtype=np.float64)
        result = normalize_image(data)
        assert result.dtype == np.uint8
        assert result[0] == 0
        assert result[1] == 127
        assert result[2] == 255

    def test_shift_required(self):
        """Test normalization when shift is required."""
        data = np.array([10, 105, 200], dtype=np.float64)
        result = normalize_image(data)
        assert result.dtype == np.uint8
        assert result[0] == 0
        assert result[1] == 127  # Approximately mid-range
        assert result[2] == 255

    def test_constant_array(self):
        """Test handling of constant array (division by zero)."""
        data = np.array([5, 5, 5], dtype=np.float64)
        result = normalize_image(data)
        # When min==max, should return zeros to avoid division by zero
        expected = np.zeros(3, dtype=np.uint8)
        assert np.array_equal(result, expected)

    def test_already_normalized(self):
        """Test with data already in 0-255 range."""
        data = np.array([0, 128, 255], dtype=np.float64)
        result = normalize_image(data)
        assert result.dtype == np.uint8
        np.testing.assert_array_equal(result, [0, 128, 255])

    def test_negative_values(self):
        """Test with negative values in data."""
        data = np.array([-100, 0, 100], dtype=np.float64)
        result = normalize_image(data)
        assert result.dtype == np.uint8
        assert result[0] == 0  # -100 -> 0
        assert result[2] == 255  # 100 -> 255

    def test_large_range(self):
        """Test with large range of values."""
        data = np.array([0, 5000, 10000], dtype=np.float64)
        result = normalize_image(data)
        assert result.dtype == np.uint8
        assert result[0] == 0
        assert result[1] == 127  # ~5000 is half of 10000
        assert result[2] == 255

    def test_dtype_is_uint8(self):
        """Test that output dtype is uint8."""
        data = np.array([0.0, 127.5, 255.0], dtype=np.float64)
        result = normalize_image(data)
        assert result.dtype == np.uint8

    def test_clipping_above_255(self):
        """Test that values above 255 are clipped."""
        data = np.array([0, 127, 1000], dtype=np.float64)
        result = normalize_image(data)
        assert result[2] == 255  # Clipped to 255

    def test_clipping_below_0(self):
        """Test that values below 0 are clipped (shouldn't happen after min shift)."""
        data = np.array([-1000, -500, 0], dtype=np.float64)
        result = normalize_image(data)
        assert result[0] == 0  # Shifted and clipped

    def test_multidimensional_array(self):
        """Test normalization with 2D array."""
        data = np.array([[0, 127], [255, 64]], dtype=np.float64)
        result = normalize_image(data)
        assert result.dtype == np.uint8
        assert result.shape == data.shape

    def test_3d_array(self):
        """Test normalization with 3D array."""
        data = np.random.rand(10, 10, 3) * 1000
        result = normalize_image(data)
        assert result.dtype == np.uint8
        assert result.shape == data.shape
        assert np.min(result) == 0
        assert np.max(result) == 255


# =============================================================================
# DatacubeFragment Tests
# =============================================================================

class TestDatacubeFragment:
    """Tests for DatacubeFragment base class behavior (tested via subclasses)."""

    def test_rotation_must_be_multiple_of_90(self, tmp_path):
        """Test that non-90-degree rotation raises ValueError."""
        # Create a minimal file
        data = np.zeros((2, 3, 4), dtype=np.float32)
        file_path = tmp_path / "test.dms"

        # Write minimal elemental file
        header = ElementalDatacubeFragment.create_file_header(4, 3, 2)
        with open(file_path, "wb") as f:
            f.write(header)
            data.tofile(f)
            f.write(b"Fe\r\nCu\r\n")

        with pytest.raises(ValueError, match="Rotation must be a multiple of 90"):
            ElementalDatacubeFragment(
                str(file_path), 4, 3, 2, len(header), 45, ["Fe", "Cu"]
            )

    def test_rotation_0_dimensions(self, tmp_path):
        """Test rotated dimensions with 0 degree rotation."""
        file_path = tmp_path / "test.raw"
        file_path.touch()

        fragment = SpectralDatacubeFragment(
            str(file_path), width=100, height=50, channels=10,
            offset=0, data_type="<u2", rotation=0, rpl_meta={}, is_transposed=False
        )

        assert fragment.rotated_width == 100
        assert fragment.rotated_height == 50

    def test_rotation_90_swaps_dimensions(self, tmp_path):
        """Test rotated dimensions with 90 degree rotation."""
        file_path = tmp_path / "test.raw"
        file_path.touch()

        fragment = SpectralDatacubeFragment(
            str(file_path), width=100, height=50, channels=10,
            offset=0, data_type="<u2", rotation=90, rpl_meta={}, is_transposed=False
        )

        assert fragment.rotated_width == 50
        assert fragment.rotated_height == 100

    def test_rotation_180_keeps_dimensions(self, tmp_path):
        """Test rotated dimensions with 180 degree rotation."""
        file_path = tmp_path / "test.raw"
        file_path.touch()

        fragment = SpectralDatacubeFragment(
            str(file_path), width=100, height=50, channels=10,
            offset=0, data_type="<u2", rotation=180, rpl_meta={}, is_transposed=False
        )

        assert fragment.rotated_width == 100
        assert fragment.rotated_height == 50

    def test_rotation_360_normalized_to_0(self, tmp_path):
        """Test that 360 degree rotation is normalized to 0."""
        file_path = tmp_path / "test.raw"
        file_path.touch()

        fragment = SpectralDatacubeFragment(
            str(file_path), width=100, height=50, channels=10,
            offset=0, data_type="<u2", rotation=360, rpl_meta={}, is_transposed=False
        )

        assert fragment.rotation == 0
        assert fragment.rotated_width == 100
        assert fragment.rotated_height == 50


# =============================================================================
# ElementalDatacubeFragment Tests
# =============================================================================

class TestElementalDatacubeFragment:
    """Tests for ElementalDatacubeFragment class."""

    @pytest.fixture
    def sample_elemental_file(self, tmp_path):
        """Create a sample elemental datacube file."""
        width, height, channels = 4, 3, 2
        data = np.arange(width * height * channels, dtype=np.float32).reshape(
            (channels, height, width)
        )

        file_path = tmp_path / "test.dms"
        header = ElementalDatacubeFragment.create_file_header(width, height, channels)
        footer = ElementalDatacubeFragment.create_file_footer(["Fe", "Cu"])

        with open(file_path, "wb") as f:
            f.write(header)
            data.tofile(f)
            f.write(footer)

        return file_path, data, ["Fe", "Cu"]

    def test_from_file_parses_correctly(self, sample_elemental_file):
        """Test that from_file correctly parses header and footer."""
        file_path, expected_data, expected_elements = sample_elemental_file

        fragment = ElementalDatacubeFragment.from_file(str(file_path))

        assert fragment.width == 4
        assert fragment.height == 3
        assert fragment.channels == 2
        assert fragment.elements == expected_elements
        assert fragment.rotation == 0

    def test_from_file_with_rotation(self, sample_elemental_file):
        """Test from_file with rotation parameter."""
        file_path, _, _ = sample_elemental_file

        fragment = ElementalDatacubeFragment.from_file(str(file_path), rotation=90)

        assert fragment.rotation == 90
        assert fragment.rotated_width == 3
        assert fragment.rotated_height == 4

    def test_load_datacube_returns_correct_shape(self, sample_elemental_file):
        """Test that load_datacube returns memmap with (C, H, W) shape."""
        file_path, expected_data, _ = sample_elemental_file

        fragment = ElementalDatacubeFragment.from_file(str(file_path))
        memmap = fragment.load_datacube()

        assert memmap.shape == (2, 3, 4)
        np.testing.assert_array_equal(memmap, expected_data)

    def test_are_compatible_same_elements(self, sample_elemental_file, tmp_path):
        """Test are_compatible returns True for matching elements."""
        file_path, _, _ = sample_elemental_file

        # Create second file with same elements
        file_path2 = tmp_path / "test2.dms"
        data2 = np.zeros((2, 3, 4), dtype=np.float32)
        header = ElementalDatacubeFragment.create_file_header(4, 3, 2)
        footer = ElementalDatacubeFragment.create_file_footer(["Fe", "Cu"])

        with open(file_path2, "wb") as f:
            f.write(header)
            data2.tofile(f)
            f.write(footer)

        fragment1 = ElementalDatacubeFragment.from_file(str(file_path))
        fragment2 = ElementalDatacubeFragment.from_file(str(file_path2))

        assert fragment1.are_compatible(fragment2) is True

    def test_are_compatible_different_elements(self, sample_elemental_file, tmp_path):
        """Test are_compatible returns False for different elements."""
        file_path, _, _ = sample_elemental_file

        # Create second file with different elements
        file_path2 = tmp_path / "test2.dms"
        data2 = np.zeros((2, 3, 4), dtype=np.float32)
        header = ElementalDatacubeFragment.create_file_header(4, 3, 2)
        footer = ElementalDatacubeFragment.create_file_footer(["Au", "Ag"])

        with open(file_path2, "wb") as f:
            f.write(header)
            data2.tofile(f)
            f.write(footer)

        fragment1 = ElementalDatacubeFragment.from_file(str(file_path))
        fragment2 = ElementalDatacubeFragment.from_file(str(file_path2))

        assert fragment1.are_compatible(fragment2) is False

    def test_are_compatible_different_channel_count(self, sample_elemental_file, tmp_path):
        """Test are_compatible returns False for different channel counts."""
        file_path, _, _ = sample_elemental_file

        # Create second file with 3 channels
        file_path2 = tmp_path / "test2.dms"
        data2 = np.zeros((3, 3, 4), dtype=np.float32)
        header = ElementalDatacubeFragment.create_file_header(4, 3, 3)
        footer = ElementalDatacubeFragment.create_file_footer(["Fe", "Cu", "Au"])

        with open(file_path2, "wb") as f:
            f.write(header)
            data2.tofile(f)
            f.write(footer)

        fragment1 = ElementalDatacubeFragment.from_file(str(file_path))
        fragment2 = ElementalDatacubeFragment.from_file(str(file_path2))

        assert fragment1.are_compatible(fragment2) is False

    def test_are_compatible_non_elemental(self, sample_elemental_file, tmp_path):
        """Test are_compatible returns False for non-ElementalDatacubeFragment."""
        file_path, _, _ = sample_elemental_file
        fragment = ElementalDatacubeFragment.from_file(str(file_path))

        # Create a spectral fragment
        spectral_file = tmp_path / "test.raw"
        spectral_file.touch()
        spectral = SpectralDatacubeFragment(
            str(spectral_file), 4, 3, 2, 0, "<u2", 0, {}, False
        )

        assert fragment.are_compatible(spectral) is False

    def test_is_spectral_returns_false(self, sample_elemental_file):
        """Test that is_spectral returns False."""
        file_path, _, _ = sample_elemental_file
        fragment = ElementalDatacubeFragment.from_file(str(file_path))

        assert fragment.is_spectral() is False

    def test_create_file_header_format(self):
        """Test header format is correct."""
        header = ElementalDatacubeFragment.create_file_header(100, 50, 10)

        lines = header.decode("ascii").split("\n")
        assert lines[0] == "2"
        assert "100" in lines[1]
        assert "50" in lines[1]
        assert "10" in lines[1]

    def test_create_file_footer_format(self):
        """Test footer format is correct."""
        footer = ElementalDatacubeFragment.create_file_footer(["Fe", "Cu", "Au"])

        assert footer == b"Fe\r\nCu\r\nAu\r\n"

    def test_write_file(self, tmp_path):
        """Test write_file creates valid file."""
        file_path = tmp_path / "output.dms"
        elements = ["Fe", "Cu"]

        def fill_data(memmap):
            memmap[:] = np.arange(memmap.size, dtype=np.float32).reshape(memmap.shape)

        fragment = ElementalDatacubeFragment.write_file(
            str(file_path), 4, 3, 2, elements, fill_data
        )

        assert fragment.width == 4
        assert fragment.height == 3
        assert fragment.channels == 2
        assert fragment.elements == elements

        # Verify data was written correctly
        memmap = fragment.load_datacube()
        expected = np.arange(24, dtype=np.float32).reshape((2, 3, 4))
        np.testing.assert_array_equal(memmap, expected)

    def test_create_greyscale_projection(self, sample_elemental_file):
        """Test greyscale projection for elemental data."""
        file_path, _, _ = sample_elemental_file
        fragment = ElementalDatacubeFragment.from_file(str(file_path))

        projection = fragment.create_greyscale_projection()

        assert projection.dtype == np.uint8
        assert projection.shape == (3, 4)  # (H, W)


# =============================================================================
# SpectralDatacubeFragment Tests
# =============================================================================

class TestSpectralDatacubeFragment:
    """Tests for SpectralDatacubeFragment class."""

    def test_parse_rpl_file(self, sample_rpl_file):
        """Test RPL file parsing."""
        meta = SpectralDatacubeFragment.parse_rpl_file(str(sample_rpl_file))

        assert meta["width"] == 10
        assert meta["height"] == 8
        assert meta["depth"] == 4
        assert meta["offset"] == 0
        assert meta["data-Length"] == 2
        assert meta["data-type"] == "unsigned"
        assert meta["byte-order"] == "little-endian"

    def test_from_file_parses_correctly(self, sample_spectral_file):
        """Test from_file correctly parses RPL and creates fragment."""
        raw_path, rpl_path, _ = sample_spectral_file

        fragment = SpectralDatacubeFragment.from_file(str(raw_path), str(rpl_path))

        assert fragment.width == 10
        assert fragment.height == 8
        assert fragment.channels == 4
        assert fragment.data_type == "<u2"
        assert fragment.is_transposed is False

    def test_from_file_with_rotation(self, sample_spectral_file):
        """Test from_file with rotation parameter."""
        raw_path, rpl_path, _ = sample_spectral_file

        fragment = SpectralDatacubeFragment.from_file(
            str(raw_path), str(rpl_path), rotation=90
        )

        assert fragment.rotation == 90
        assert fragment.rotated_width == 8
        assert fragment.rotated_height == 10

    def test_from_file_signed_big_endian(self, tmp_path):
        """Test from_file with signed big-endian data."""
        rpl_path = tmp_path / "test.rpl"
        rpl_content = """width       	5
height      	5
depth       	2
offset      	0
data-Length 	4
data-type   	signed
byte-order  	big-endian
"""
        rpl_path.write_text(rpl_content)

        raw_path = tmp_path / "test.raw"
        data = np.zeros((5, 5, 2), dtype=">i4")
        data.tofile(str(raw_path))

        fragment = SpectralDatacubeFragment.from_file(str(raw_path), str(rpl_path))

        assert fragment.data_type == ">i4"

    def test_from_file_unsupported_data_length(self, tmp_path):
        """Test from_file raises error for unsupported data length."""
        rpl_path = tmp_path / "test.rpl"
        rpl_content = """width       	5
height      	5
depth       	2
offset      	0
data-Length 	3
data-type   	unsigned
byte-order  	little-endian
"""
        rpl_path.write_text(rpl_content)
        raw_path = tmp_path / "test.raw"
        raw_path.touch()

        with pytest.raises(ValueError, match="Unsupported element size: 3 bytes"):
            SpectralDatacubeFragment.from_file(str(raw_path), str(rpl_path))

    def test_is_spectral_returns_true(self, sample_spectral_file):
        """Test that is_spectral returns True."""
        raw_path, rpl_path, _ = sample_spectral_file
        fragment = SpectralDatacubeFragment.from_file(str(raw_path), str(rpl_path))

        assert fragment.is_spectral() is True

    def test_load_datacube_non_transposed(self, sample_spectral_file):
        """Test load_datacube returns (H, W, C) for non-transposed."""
        raw_path, rpl_path, expected_data = sample_spectral_file
        fragment = SpectralDatacubeFragment.from_file(str(raw_path), str(rpl_path))

        memmap = fragment.load_datacube()

        assert memmap.shape == (8, 10, 4)
        np.testing.assert_array_equal(memmap, expected_data)

    def test_load_datacube_transposed(self, tmp_path):
        """Test load_datacube returns (C, H, W) for transposed."""
        raw_path = tmp_path / "test.raw"
        data = np.arange(4 * 8 * 10, dtype=np.uint16).reshape((4, 8, 10))
        data.tofile(str(raw_path))

        fragment = SpectralDatacubeFragment(
            str(raw_path), width=10, height=8, channels=4,
            offset=0, data_type="<u2", rotation=0, rpl_meta={}, is_transposed=True
        )

        memmap = fragment.load_datacube()

        assert memmap.shape == (4, 8, 10)
        np.testing.assert_array_equal(memmap, data)

    def test_create_transposed_version_new_file(self, sample_spectral_file):
        """Test create_transposed_version creates new transposed file."""
        raw_path, rpl_path, original_data = sample_spectral_file
        fragment = SpectralDatacubeFragment.from_file(str(raw_path), str(rpl_path))

        transposed = fragment.create_transposed_version(check_existing=False)

        assert transposed.is_transposed is True
        assert "_transposed.raw" in transposed.datacube_file

        # Verify data is correctly transposed
        transposed_data = transposed.load_datacube()
        expected = original_data.transpose(2, 0, 1)
        np.testing.assert_array_equal(transposed_data, expected)

    def test_create_transposed_version_already_transposed(self, tmp_path):
        """Test create_transposed_version returns self if already transposed."""
        raw_path = tmp_path / "test.raw"
        raw_path.touch()

        fragment = SpectralDatacubeFragment(
            str(raw_path), width=10, height=8, channels=4,
            offset=0, data_type="<u2", rotation=0, rpl_meta={}, is_transposed=True
        )

        result = fragment.create_transposed_version()

        assert result is fragment

    def test_create_transposed_version_reuses_existing(self, sample_spectral_file):
        """Test create_transposed_version reuses existing valid file."""
        raw_path, rpl_path, original_data = sample_spectral_file
        fragment = SpectralDatacubeFragment.from_file(str(raw_path), str(rpl_path))

        # Create transposed file first time
        transposed1 = fragment.create_transposed_version(check_existing=False)

        # Create again - should reuse
        transposed2 = fragment.create_transposed_version(check_existing=True)

        assert transposed2.datacube_file == transposed1.datacube_file
        assert transposed2.is_transposed is True

    def test_create_transposed_version_wrong_size_retransposes(
            self, sample_spectral_file, tmp_path
    ):
        """Test create_transposed_version re-transposes if existing file has wrong size."""
        raw_path, rpl_path, _ = sample_spectral_file
        fragment = SpectralDatacubeFragment.from_file(str(raw_path), str(rpl_path))

        # Create a wrong-sized transposed file
        transposed_path = SpectralDatacubeFragment.get_transposed_path(str(raw_path))
        with open(transposed_path, "wb") as f:
            f.write(b"wrong size data")

        # Should re-transpose due to wrong size
        transposed = fragment.create_transposed_version(check_existing=True)

        assert transposed.is_transposed is True
        # Verify correct size now
        expected_size = 10 * 8 * 4 * 2  # W * H * C * bytes_per_element
        assert os.path.getsize(transposed.datacube_file) == expected_size

    def test_get_transposed_path(self):
        """Test get_transposed_path returns correct path."""
        path = SpectralDatacubeFragment.get_transposed_path("/path/to/data.raw")

        assert path == "/path/to/data_transposed.raw"

    def test_are_compatible_same_type_channels(self, sample_spectral_file, tmp_path):
        """Test are_compatible returns True for matching type and channels."""
        raw_path, rpl_path, _ = sample_spectral_file
        fragment1 = SpectralDatacubeFragment.from_file(str(raw_path), str(rpl_path))

        # Create second compatible file
        raw_path2 = tmp_path / "test2.raw"
        data2 = np.zeros((8, 10, 4), dtype=np.uint16)
        data2.tofile(str(raw_path2))

        fragment2 = SpectralDatacubeFragment.from_file(str(raw_path2), str(rpl_path))

        assert fragment1.are_compatible(fragment2) is True

    def test_are_compatible_different_channels(self, sample_spectral_file, tmp_path):
        """Test are_compatible returns False for different channel counts."""
        raw_path, rpl_path, _ = sample_spectral_file
        fragment1 = SpectralDatacubeFragment.from_file(str(raw_path), str(rpl_path))

        # Create second file with different channels
        rpl_path2 = tmp_path / "test2.rpl"
        rpl_content = """width       	10
height      	8
depth       	8
offset      	0
data-Length 	2
data-type   	unsigned
byte-order  	little-endian
"""
        rpl_path2.write_text(rpl_content)

        raw_path2 = tmp_path / "test2.raw"
        data2 = np.zeros((8, 10, 8), dtype=np.uint16)
        data2.tofile(str(raw_path2))

        fragment2 = SpectralDatacubeFragment.from_file(str(raw_path2), str(rpl_path2))

        assert fragment1.are_compatible(fragment2) is False

    def test_are_compatible_different_dtype(self, sample_spectral_file, tmp_path):
        """Test are_compatible returns False for different data types."""
        raw_path, rpl_path, _ = sample_spectral_file
        fragment1 = SpectralDatacubeFragment.from_file(str(raw_path), str(rpl_path))

        # Create second file with different dtype
        rpl_path2 = tmp_path / "test2.rpl"
        rpl_content = """width       	10
height      	8
depth       	4
offset      	0
data-Length 	4
data-type   	unsigned
byte-order  	little-endian
"""
        rpl_path2.write_text(rpl_content)

        raw_path2 = tmp_path / "test2.raw"
        data2 = np.zeros((8, 10, 4), dtype=np.uint32)
        data2.tofile(str(raw_path2))

        fragment2 = SpectralDatacubeFragment.from_file(str(raw_path2), str(rpl_path2))

        assert fragment1.are_compatible(fragment2) is False

    def test_are_compatible_non_spectral(self, sample_spectral_file, tmp_path):
        """Test are_compatible returns False for non-SpectralDatacubeFragment."""
        raw_path, rpl_path, _ = sample_spectral_file
        fragment = SpectralDatacubeFragment.from_file(str(raw_path), str(rpl_path))

        # Create elemental fragment
        elemental_path = tmp_path / "test.dms"
        header = ElementalDatacubeFragment.create_file_header(4, 3, 2)
        data = np.zeros((2, 3, 4), dtype=np.float32)
        footer = ElementalDatacubeFragment.create_file_footer(["Fe", "Cu"])

        with open(elemental_path, "wb") as f:
            f.write(header)
            data.tofile(f)
            f.write(footer)

        elemental = ElementalDatacubeFragment.from_file(str(elemental_path))

        assert fragment.are_compatible(elemental) is False

    def test_write_rpl_file(self, tmp_path):
        """Test write_rpl_file creates correct metadata file."""
        rpl_path = tmp_path / "output.rpl"
        rpl_meta = {
            "depth": 4,
            "data-Length": 2,
            "data-type": "unsigned",
            "byte-order": "little-endian",
        }

        SpectralDatacubeFragment.write_rpl_file(str(rpl_path), rpl_meta, 100, 50)

        # Parse back and verify
        parsed = SpectralDatacubeFragment.parse_rpl_file(str(rpl_path))
        assert parsed["width"] == 100
        assert parsed["height"] == 50
        assert parsed["offset"] == 0
        assert parsed["depth"] == 4

    def test_write_file(self, tmp_path):
        """Test write_file creates valid raw and rpl files."""
        raw_path = tmp_path / "output.raw"
        rpl_path = tmp_path / "output.rpl"
        rpl_meta = {
            "depth": 4,
            "data-Length": 2,
            "data-type": "unsigned",
            "byte-order": "little-endian",
        }

        def fill_data(memmap):
            memmap[:] = np.arange(memmap.size, dtype=np.uint16).reshape(memmap.shape)

        fragment = SpectralDatacubeFragment.write_file(
            str(raw_path), str(rpl_path), rpl_meta, "<u2", 10, 8, 4, fill_data
        )

        assert fragment.width == 10
        assert fragment.height == 8
        assert fragment.channels == 4

        # Verify data
        memmap = fragment.load_datacube()
        expected = np.arange(10 * 8 * 4, dtype=np.uint16).reshape((8, 10, 4))
        np.testing.assert_array_equal(memmap, expected)

    def test_create_greyscale_projection(self, sample_spectral_file):
        """Test greyscale projection for spectral data."""
        raw_path, rpl_path, _ = sample_spectral_file
        fragment = SpectralDatacubeFragment.from_file(str(raw_path), str(rpl_path))

        projection = fragment.create_greyscale_projection()

        assert projection.dtype == np.uint8
        assert projection.shape == (8, 10)  # (H, W)
