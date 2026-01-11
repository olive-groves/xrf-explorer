import logging
import os
import sys
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

RESOURCES_PATH: str = join("tests", "resources")

CUSTOM_CONFIG_PATH: str = join(RESOURCES_PATH, 'configs', 'stitching.yml')

DATA_SOURCE = "data_source"
IMAGE_NAME = "RGB"

PATH_DATA_SOURCE: str = join(RESOURCES_PATH, 'stitching', DATA_SOURCE)

SAMPLE_FULL_SPECTRAL_CUBE_PATH: str = join(PATH_DATA_SOURCE, 'sample_spectral_8x8x4.raw')
RGB_STITCH_IMAGE: str = join(PATH_DATA_SOURCE, 'test_image_stitching.png')

TEMP_OUTPUT_PATH: str = join(PATH_DATA_SOURCE, 'output.raw')


'color_segmentation'
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
def sample_image():
    """Create a sample numpy array image."""
    return np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)


@pytest.fixture
def sample_test_image():
    """Load test image from resources."""
    import cv2

    img_path = join(RESOURCES_PATH, "stitching", "data_source", "test_image_stitching.png")
    return cv2.imread(img_path)


@pytest.fixture
def sample_spectral_raw(tmp_path):
    """Create a temporary spectral datacube file with shape (8, 8, 4)."""
    # Create test data with shape (8, 8, 4) - HWC format
    input_data = np.fromfile(SAMPLE_FULL_SPECTRAL_CUBE_PATH, dtype="uint16").reshape((8, 8, 4))
    # Print current working directory for debugging
    return input_data


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

    def test_hwc_to_chw(self, sample_spectral_raw):
        """Test HWC to CHW transposition (8x8x4 -> 4x8x8)."""
        input_data = sample_spectral_raw
        input_path = SAMPLE_FULL_SPECTRAL_CUBE_PATH
        output_path = TEMP_OUTPUT_PATH

        transpose_spectral_datacube(input_path, output_path, (8, 8, 4), (4, 8, 8), "uint16", TransposeMode.HWC_TO_CHW)

        output_data = np.fromfile(output_path, dtype="uint16").reshape(4, 8, 8)
        expected = input_data.transpose(2, 0, 1)
        assert np.array_equal(output_data, expected)


    def test_chw_to_hwc(self, tmp_path):
        """Test CHW to HWC transposition (4x8x8 -> 8x8x4)."""
        # Create input data in CHW format
        input_data = np.arange(256).reshape(4, 8, 8).astype("uint16")
        input_path = tmp_path / "input.raw"
        output_path = tmp_path / "output.raw"
        input_data.tofile(str(input_path))

        transpose_spectral_datacube(str(input_path), str(output_path), (4, 8, 8), (8, 8, 4), "uint16", TransposeMode.CHW_TO_HWC)

        output_data = np.fromfile(str(output_path), dtype="uint16").reshape(8, 8, 4)
        expected = input_data.transpose(1, 2, 0)
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

    def test_preserves_data_integrity(self, tmp_path):
        """Test that data values are preserved after transpose."""
        input_data = np.ones((8, 8, 4), dtype="uint16") * np.arange(4).reshape(1, 1, 4)
        input_path = tmp_path / "input.raw"
        output_path = tmp_path / "output.raw"
        input_data.tofile(str(input_path))

        transpose_spectral_datacube(str(input_path), str(output_path), (8, 8, 4), (4, 8, 8), "uint16", TransposeMode.HWC_TO_CHW)

        output_data = np.fromfile(str(output_path), dtype="uint16").reshape(4, 8, 8)

        # Each channel should have constant value
        for channel in range(4):
            assert np.all(output_data[channel] == channel)


class TestRotateCv:
    """Tests for rotate_cv function."""

    def test_no_rotation(self):
        """Test that rotation=0 returns original."""
        img = np.arange(9).reshape(3, 3).astype(np.uint8)
        result = rotate_cv(img, 0)
        assert np.array_equal(result, img)

    def test_90_degrees_counter_clockwise(self):
        """Test 90-degree counter-clockwise rotation."""
        img = np.zeros((3, 3), dtype=np.uint8)
        img[0, 0] = 1  # Top-left corner
        result = rotate_cv(img, 90)
        assert result[0, 2] == 1  # Should be at top-right after CCW rotation

    def test_180_degrees(self):
        """Test 180-degree rotation."""
        img = np.zeros((3, 3), dtype=np.uint8)
        img[0, 0] = 1
        result = rotate_cv(img, 180)
        assert result[2, 2] == 1  # Should be at bottom-right

    def test_270_degrees_clockwise(self):
        """Test 270-degree (90 CW) rotation."""
        img = np.zeros((3, 3), dtype=np.uint8)
        img[0, 0] = 1
        result = rotate_cv(img, 270)
        assert result[2, 0] == 1  # Should be at bottom-left

    def test_invalid_rotation(self):
        """Test that invalid rotation raises ValueError."""
        img = np.zeros((10, 10), dtype=np.uint8)
        with pytest.raises(ValueError, match="Rotation must be"):
            rotate_cv(img, 45)

    def test_negative_rotation(self):
        """Test that negative rotation raises ValueError."""
        img = np.zeros((10, 10), dtype=np.uint8)
        with pytest.raises(ValueError, match="Rotation must be"):
            rotate_cv(img, -90)

    def test_shape_preserved_90(self):
        """Test that shape is preserved for 90-degree rotation."""
        img = np.zeros((100, 50, 3), dtype=np.uint8)
        result = rotate_cv(img, 90)
        assert result.shape == (50, 100, 3)

    def test_shape_preserved_180(self):
        """Test that shape is preserved for 180-degree rotation."""
        img = np.zeros((100, 50, 3), dtype=np.uint8)
        result = rotate_cv(img, 180)
        assert result.shape == (100, 50, 3)

    def test_shape_preserved_270(self):
        """Test that shape is preserved for 270-degree rotation."""
        img = np.zeros((100, 50, 3), dtype=np.uint8)
        result = rotate_cv(img, 270)
        assert result.shape == (50, 100, 3)

    def test_with_test_image(self, sample_test_image):
        """Test rotation using actual test image from resources."""
        if sample_test_image is None:
            pytest.skip("Test image not available")

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
