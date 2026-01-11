from __future__ import annotations

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock, patch, call
import os
from os.path import join

from xrf_explorer.server.stitcher.stitcher import DatacubeStitcher
from xrf_explorer.server.stitcher.cube_fragments import (
    DatacubeFragment,
    ElementalDatacubeFragment,
    SpectralDatacubeFragment,
)
from xrf_explorer.server.stitcher.helper import WarpSelection, Dimensions
from xrf_explorer.server.stitcher.transpose_state import (
    TransposeStateManager,
    TransposeState,
    TransposeInfo,
)


@pytest.fixture
def mock_warp_selection_pair():
    """Create a pair of mock WarpSelection objects for testing."""
    src = Mock(spec=WarpSelection)
    src.get_points = Mock(
        return_value=np.array(
            [[0, 0], [50, 0], [50, 50], [0, 50]], dtype=np.float32
        )
    )
    dst = Mock(spec=WarpSelection)
    dst.get_points = Mock(
        return_value=np.array(
            [[0, 0], [50, 0], [50, 50], [0, 50]], dtype=np.float32
        )
    )
    return (src, dst)


@pytest.fixture
def mock_elemental_fragment():
    """Create a mock ElementalDatacubeFragment."""
    fragment = Mock(spec=ElementalDatacubeFragment)
    fragment.are_compatible = Mock(return_value=True)
    fragment.channels = 5
    fragment.rotation = 0
    fragment.height = 50
    fragment.width = 50
    fragment.is_spectral = Mock(return_value=False)
    fragment.elements = ["Fe", "Cu", "Au", "Ag", "Pb"]
    fragment.load_datacube = Mock(
        return_value=np.ones((5, 50, 50), dtype=np.float32)
    )
    return fragment


@pytest.fixture
def mock_spectral_fragment():
    """Create a mock SpectralDatacubeFragment."""
    fragment = Mock(spec=SpectralDatacubeFragment)
    fragment.are_compatible = Mock(return_value=True)
    fragment.channels = 100
    fragment.rotation = 0
    fragment.height = 50
    fragment.width = 50
    fragment.is_spectral = Mock(return_value=True)
    fragment.data_type = "<u2"
    fragment.rpl_meta = {"width": 50, "height": 50, "depth": 100}
    fragment.datacube_file = "/path/to/spectral.raw"
    fragment.load_datacube = Mock(
        return_value=np.ones((100, 50, 50), dtype=np.uint16)
    )
    return fragment


class TestDatacubeStitcherInit:
    """Tests for DatacubeStitcher.__init__"""

    def test_no_fragments_raises_error(self):
        """Should raise ValueError when no fragments provided."""
        with pytest.raises(ValueError, match="No fragments provided"):
            DatacubeStitcher(
                fragments=[],
                intensity_scales=[],
                points=[],
                frame=Dimensions(100, 100),
            )

    def test_none_fragments_raises_error(self):
        """Should raise ValueError when fragments is None."""
        with pytest.raises(ValueError, match="No fragments provided"):
            DatacubeStitcher(
                fragments=None,
                intensity_scales=[],
                points=[],
                frame=Dimensions(100, 100),
            )

    def test_too_many_fragments_raises_error(self, mock_warp_selection_pair):
        """Should raise ValueError when more than 32 fragments."""
        fragments = [Mock(spec=DatacubeFragment) for _ in range(33)]
        with pytest.raises(ValueError, match="Too many fragments provided, maximum is 32"):
            DatacubeStitcher(
                fragments=fragments,
                intensity_scales=[1.0] * 33,
                points=[mock_warp_selection_pair] * 33,
                frame=Dimensions(100, 100),
            )

    def test_mismatched_intensity_scales_raises_error(
        self, mock_elemental_fragment, mock_warp_selection_pair
    ):
        """Should raise ValueError when intensity_scales length doesn't match."""
        with pytest.raises(ValueError, match="must match"):
            DatacubeStitcher(
                fragments=[mock_elemental_fragment, mock_elemental_fragment],
                intensity_scales=[1.0],  # Only one scale for two fragments
                points=[mock_warp_selection_pair, mock_warp_selection_pair],
                frame=Dimensions(100, 100),
            )

    def test_mismatched_points_raises_error(
        self, mock_elemental_fragment, mock_warp_selection_pair
    ):
        """Should raise ValueError when points length doesn't match."""
        with pytest.raises(ValueError, match="must match"):
            DatacubeStitcher(
                fragments=[mock_elemental_fragment, mock_elemental_fragment],
                intensity_scales=[1.0, 1.0],
                points=[mock_warp_selection_pair],  # Only one point set
                frame=Dimensions(100, 100),
            )

    def test_incompatible_datacubes_raises_error(self, mock_warp_selection_pair):
        """Should raise ValueError when datacubes are incompatible."""
        fragment1 = Mock(spec=DatacubeFragment)
        fragment2 = Mock(spec=DatacubeFragment)
        fragment1.are_compatible = Mock(return_value=False)

        with pytest.raises(ValueError, match="Incompatible datacubes"):
            DatacubeStitcher(
                fragments=[fragment1, fragment2],
                intensity_scales=[1.0, 1.0],
                points=[mock_warp_selection_pair, mock_warp_selection_pair],
                frame=Dimensions(100, 100),
            )

    def test_valid_initialization(
        self, mock_elemental_fragment, mock_warp_selection_pair
    ):
        """Should initialize correctly with valid inputs."""
        stitcher = DatacubeStitcher(
            fragments=[mock_elemental_fragment, mock_elemental_fragment],
            intensity_scales=[1.0, 1.0],
            points=[mock_warp_selection_pair, mock_warp_selection_pair],
            frame=Dimensions(100, 200),
            scalar=2.0,
            outputdir="/tmp",
            data_source="test_source",
        )

        assert stitcher.scaled_width == 200
        assert stitcher.scaled_height == 400
        assert stitcher.base_cube == mock_elemental_fragment
        assert len(stitcher.perspective_matrices) == 2
        assert stitcher.outputdir == "/tmp"
        assert stitcher.data_source == "test_source"
        assert stitcher.transposed_files == []

    def test_scalar_default_value(
        self, mock_elemental_fragment, mock_warp_selection_pair
    ):
        """Should use default scalar of 1.0."""
        stitcher = DatacubeStitcher(
            fragments=[mock_elemental_fragment],
            intensity_scales=[1.0],
            points=[mock_warp_selection_pair],
            frame=Dimensions(100, 100),
        )

        assert stitcher.scalar == 1.0
        assert stitcher.scaled_width == 100
        assert stitcher.scaled_height == 100


class TestStitchGreyscales:
    """Tests for DatacubeStitcher.stitch_greyscales"""

    def test_mismatched_images_raises_error(
        self, mock_elemental_fragment, mock_warp_selection_pair
    ):
        """Should raise ValueError when image count doesn't match points."""
        stitcher = DatacubeStitcher(
            fragments=[mock_elemental_fragment],
            intensity_scales=[1.0],
            points=[mock_warp_selection_pair],
            frame=Dimensions(100, 100),
        )

        images = [np.zeros((50, 50)), np.zeros((50, 50))]  # Two images, one point

        with pytest.raises(ValueError, match="must match"):
            stitcher.stitch_greyscales(images)

    def test_stitch_single_image(
        self, mock_elemental_fragment, mock_warp_selection_pair
    ):
        """Should stitch a single greyscale image."""
        stitcher = DatacubeStitcher(
            fragments=[mock_elemental_fragment],
            intensity_scales=[1.0],
            points=[mock_warp_selection_pair],
            frame=Dimensions(100, 100),
        )

        image = np.ones((50, 50), dtype=np.float32) * 128
        result = stitcher.stitch_greyscales([image])

        assert result.shape == (100, 100)
        assert result.dtype == np.float32
        # Border pixels should be 0 (replaced from -1)
        assert np.any(result == 0)

    def test_stitch_with_intensity_scale(
        self, mock_elemental_fragment, mock_warp_selection_pair
    ):
        """Should apply intensity scaling to stitched greyscales."""
        stitcher = DatacubeStitcher(
            fragments=[mock_elemental_fragment],
            intensity_scales=[2.0],
            points=[mock_warp_selection_pair],
            frame=Dimensions(100, 100),
        )

        image = np.ones((50, 50), dtype=np.float32) * 50
        result = stitcher.stitch_greyscales([image])

        # Non-border pixels should be scaled
        non_border = result[result > 0]
        assert len(non_border) > 0
        assert np.allclose(non_border, 100.0, atol=1)

    def test_stitch_with_rotation(self, mock_warp_selection_pair):
        """Should apply rotation before warping."""
        fragment = Mock(spec=ElementalDatacubeFragment)
        fragment.are_compatible = Mock(return_value=True)
        fragment.channels = 2
        fragment.rotation = 90  # 90-degree rotation
        fragment.height = 50
        fragment.width = 50
        fragment.is_spectral = Mock(return_value=False)

        stitcher = DatacubeStitcher(
            fragments=[fragment],
            intensity_scales=[1.0],
            points=[mock_warp_selection_pair],
            frame=Dimensions(100, 100),
        )

        image = np.ones((50, 50), dtype=np.float32)
        result = stitcher.stitch_greyscales([image])

        assert result.shape == (100, 100)

    def test_stitch_multiple_images(
        self, mock_elemental_fragment, mock_warp_selection_pair
    ):
        """Should stitch multiple images together."""
        stitcher = DatacubeStitcher(
            fragments=[mock_elemental_fragment, mock_elemental_fragment],
            intensity_scales=[1.0, 0.5],
            points=[mock_warp_selection_pair, mock_warp_selection_pair],
            frame=Dimensions(100, 100),
        )

        images = [
            np.ones((50, 50), dtype=np.float32) * 100,
            np.ones((50, 50), dtype=np.float32) * 200,
        ]
        result = stitcher.stitch_greyscales(images)

        assert result.shape == (100, 100)


class TestPrecalculateMasks:
    """Tests for DatacubeStitcher._precalculate_masks"""

    def test_creates_correct_number_of_masks(
        self, mock_elemental_fragment, mock_warp_selection_pair
    ):
        """Should create one mask per fragment."""
        stitcher = DatacubeStitcher(
            fragments=[mock_elemental_fragment, mock_elemental_fragment],
            intensity_scales=[1.0, 1.0],
            points=[mock_warp_selection_pair, mock_warp_selection_pair],
            frame=Dimensions(100, 100),
        )

        masks = stitcher._precalculate_masks()

        assert len(masks) == 2
        assert all(mask.dtype == bool for mask in masks)
        assert all(mask.shape == (100, 100) for mask in masks)

    def test_masks_with_rotation(self, mock_warp_selection_pair):
        """Should handle fragment rotation in mask calculation."""
        fragment = Mock(spec=ElementalDatacubeFragment)
        fragment.are_compatible = Mock(return_value=True)
        fragment.channels = 2
        fragment.rotation = 90
        fragment.height = 30
        fragment.width = 50

        stitcher = DatacubeStitcher(
            fragments=[fragment],
            intensity_scales=[1.0],
            points=[mock_warp_selection_pair],
            frame=Dimensions(100, 100),
        )

        masks = stitcher._precalculate_masks()

        assert len(masks) == 1
        assert masks[0].shape == (100, 100)
        # Some pixels should be True (inside the warped region)
        assert np.any(masks[0])


class TestFillSubsetLayers:
    """Tests for DatacubeStitcher.fill_subset_layers"""

    def test_fills_channel_range_elemental(
        self, mock_elemental_fragment, mock_warp_selection_pair
    ):
        """Should fill specified channel range for elemental data."""
        stitcher = DatacubeStitcher(
            fragments=[mock_elemental_fragment],
            intensity_scales=[1.0],
            points=[mock_warp_selection_pair],
            frame=Dimensions(100, 100),
        )

        input_map = np.ones((5, 50, 50), dtype=np.float32) * 10
        output_map = np.zeros((5, 100, 100), dtype=np.float32)
        masks = [np.ones((100, 100), dtype=bool)]

        stitcher.fill_subset_layers([input_map], output_map, masks, 0, 3)

        # Channels 0-2 should have data
        assert not np.all(output_map[:3] == 0)
        # Channels 3-4 should still be zeros
        assert np.all(output_map[3:] == 0)

    def test_fills_channel_range_spectral(
        self, mock_spectral_fragment, mock_warp_selection_pair
    ):
        """Should fill specified channel range for spectral data with clipping."""
        mock_spectral_fragment.is_spectral = Mock(return_value=True)

        stitcher = DatacubeStitcher(
            fragments=[mock_spectral_fragment],
            intensity_scales=[1.0],
            points=[mock_warp_selection_pair],
            frame=Dimensions(100, 100),
        )

        input_map = np.ones((100, 50, 50), dtype=np.float32) * 300  # > 255
        output_map = np.zeros((100, 100, 100), dtype=np.uint16)
        masks = [np.ones((100, 100), dtype=bool)]

        stitcher.fill_subset_layers([input_map], output_map, masks, 0, 5)

        # Values should be clipped to 255 for spectral data
        filled_region = output_map[:5][output_map[:5] > 0]
        assert len(filled_region) > 0
        assert np.all(filled_region <= 255)

    def test_applies_intensity_scale(
        self, mock_elemental_fragment, mock_warp_selection_pair
    ):
        """Should apply intensity scaling to layers."""
        stitcher = DatacubeStitcher(
            fragments=[mock_elemental_fragment],
            intensity_scales=[2.0],
            points=[mock_warp_selection_pair],
            frame=Dimensions(50, 50),
        )

        input_map = np.ones((5, 50, 50), dtype=np.float32) * 10
        output_map = np.zeros((5, 50, 50), dtype=np.float32)
        masks = [np.ones((50, 50), dtype=bool)]

        stitcher.fill_subset_layers([input_map], output_map, masks, 0, 1)

        # Values should be scaled by 2.0
        non_zero = output_map[0][output_map[0] > 0]
        assert len(non_zero) > 0
        assert np.allclose(non_zero, 20.0, atol=1)

    def test_no_scale_when_scale_is_one(
        self, mock_elemental_fragment, mock_warp_selection_pair
    ):
        """Should not modify values when scale is 1.0."""
        stitcher = DatacubeStitcher(
            fragments=[mock_elemental_fragment],
            intensity_scales=[1.0],
            points=[mock_warp_selection_pair],
            frame=Dimensions(50, 50),
        )

        input_map = np.ones((5, 50, 50), dtype=np.float32) * 42
        output_map = np.zeros((5, 50, 50), dtype=np.float32)
        masks = [np.ones((50, 50), dtype=bool)]

        stitcher.fill_subset_layers([input_map], output_map, masks, 0, 1)

        non_zero = output_map[0][output_map[0] > 0]
        assert len(non_zero) > 0
        assert np.allclose(non_zero, 42.0, atol=1)

    def test_multiple_fragments_overlay(self, mock_warp_selection_pair):
        """Should overlay multiple fragments using masks."""
        fragment1 = Mock(spec=ElementalDatacubeFragment)
        fragment1.are_compatible = Mock(return_value=True)
        fragment1.channels = 2
        fragment1.rotation = 0
        fragment1.height = 50
        fragment1.width = 50
        fragment1.is_spectral = Mock(return_value=False)

        fragment2 = Mock(spec=ElementalDatacubeFragment)
        fragment2.are_compatible = Mock(return_value=True)
        fragment2.channels = 2
        fragment2.rotation = 0
        fragment2.height = 50
        fragment2.width = 50
        fragment2.is_spectral = Mock(return_value=False)

        stitcher = DatacubeStitcher(
            fragments=[fragment1, fragment2],
            intensity_scales=[1.0, 1.0],
            points=[mock_warp_selection_pair, mock_warp_selection_pair],
            frame=Dimensions(100, 100),
        )

        input_maps = [
            np.ones((2, 50, 50), dtype=np.float32) * 10,
            np.ones((2, 50, 50), dtype=np.float32) * 20,
        ]
        output_map = np.zeros((2, 100, 100), dtype=np.float32)
        masks = [
            np.ones((100, 100), dtype=bool),
            np.ones((100, 100), dtype=bool),
        ]

        stitcher.fill_subset_layers(input_maps, output_map, masks, 0, 1)

        # Last fragment should overwrite (mask2 values = 20)
        non_zero = output_map[0][output_map[0] > 0]
        assert len(non_zero) > 0


class TestFillLayers:
    """Tests for DatacubeStitcher.fill_layers"""

    def test_orchestrates_stitching_elemental(
        self, mock_elemental_fragment, mock_warp_selection_pair
    ):
        """Should use single worker for elemental data."""
        stitcher = DatacubeStitcher(
            fragments=[mock_elemental_fragment],
            intensity_scales=[1.0],
            points=[mock_warp_selection_pair],
            frame=Dimensions(100, 100),
        )

        output_map = np.zeros((5, 100, 100), dtype=np.float32)

        with patch.object(stitcher, "fill_subset_layers") as mock_fill:
            stitcher.fill_layers(output_map)

            mock_elemental_fragment.load_datacube.assert_called_once()
            assert mock_fill.called

    def test_orchestrates_stitching_spectral_multithread(
        self, mock_spectral_fragment, mock_warp_selection_pair
    ):
        """Should use multiple workers for spectral data."""
        stitcher = DatacubeStitcher(
            fragments=[mock_spectral_fragment],
            intensity_scales=[1.0],
            points=[mock_warp_selection_pair],
            frame=Dimensions(100, 100),
        )

        output_map = np.zeros((100, 100, 100), dtype=np.uint16)

        with patch("os.cpu_count", return_value=4):
            stitcher.fill_layers(output_map)

        mock_spectral_fragment.load_datacube.assert_called_once()


class TestStitchDatacubes:
    """Tests for DatacubeStitcher.stitch_datacubes"""

    def test_mismatched_fragments_points_raises_error(
        self, mock_elemental_fragment, mock_warp_selection_pair, tmp_path
    ):
        """Should raise ValueError when fragments and points don't match."""
        stitcher = DatacubeStitcher(
            fragments=[mock_elemental_fragment],
            intensity_scales=[1.0],
            points=[mock_warp_selection_pair],
            frame=Dimensions(100, 100),
            outputdir=str(tmp_path),
        )

        # Manually modify points to create mismatch
        stitcher.points = [mock_warp_selection_pair, mock_warp_selection_pair]

        with pytest.raises(ValueError, match="must match"):
            stitcher.stitch_datacubes()

    @patch.object(ElementalDatacubeFragment, "write_file")
    def test_elemental_stitching(
        self,
        mock_write_file,
        mock_elemental_fragment,
        mock_warp_selection_pair,
        tmp_path,
    ):
        """Should stitch elemental datacubes correctly."""
        expected_result = Mock(spec=ElementalDatacubeFragment)
        mock_write_file.return_value = expected_result

        stitcher = DatacubeStitcher(
            fragments=[mock_elemental_fragment],
            intensity_scales=[1.0],
            points=[mock_warp_selection_pair],
            frame=Dimensions(100, 100),
            outputdir=str(tmp_path),
        )

        result = stitcher.stitch_datacubes()

        mock_write_file.assert_called_once()
        call_args = mock_write_file.call_args
        assert call_args[0][0] == join(str(tmp_path), "stitched_elemental.dms")
        assert call_args[0][1] == 100  # width
        assert call_args[0][2] == 100  # height
        assert call_args[0][3] == 5  # channels
        assert result == expected_result

    @patch("xrf_explorer.server.stitcher.stitcher.transpose_spectral_datacube")
    @patch.object(SpectralDatacubeFragment, "write_rpl_file")
    @patch.object(SpectralDatacubeFragment, "from_file")
    @patch("os.path.exists")
    @patch("os.remove")
    @patch("numpy.memmap")
    def test_spectral_stitching_no_pretranspose(
        self,
        mock_memmap,
        mock_remove,
        mock_exists,
        mock_from_file,
        mock_write_rpl,
        mock_transpose,
        mock_spectral_fragment,
        mock_warp_selection_pair,
        tmp_path,
    ):
        """Should stitch spectral datacubes without pre-transpose."""
        # Setup mocks
        mock_exists.return_value = False
        class MockMemmap(np.ndarray):
            pass

        # Create array, view as subclass, and attach flush
        mmap_obj = np.zeros((100, 100, 100), dtype=np.uint16).view(MockMemmap)
        mmap_obj.flush = Mock()
        mock_memmap.return_value = mmap_obj

        transposed_frag = Mock(spec=SpectralDatacubeFragment)
        transposed_frag.datacube_file = "/path/to/transposed.raw"
        transposed_frag.is_transposed = True
        # fragment.channels = 100
        # transposed_frag.rotation = 0
        transposed_frag.height = 50
        transposed_frag.width = 50
        # fragment.is_spectral = Mock(return_value=True)
        transposed_frag.load_datacube = Mock(
            return_value=np.ones((100, 50, 50), dtype=np.uint16)
        )
        transposed_frag.rotation = 0
        mock_spectral_fragment.create_transposed_version = Mock(
            return_value=transposed_frag
        )

        expected_result = Mock(spec=SpectralDatacubeFragment)
        mock_from_file.return_value = expected_result

        stitcher = DatacubeStitcher(
            fragments=[mock_spectral_fragment],
            intensity_scales=[1.0],
            points=[mock_warp_selection_pair],
            frame=Dimensions(100, 100),
            outputdir=str(tmp_path),
        )

        result = stitcher.stitch_datacubes()

        mock_spectral_fragment.create_transposed_version.assert_called_once()
        assert mock_transpose.call_count == 1  # Output transpose back to HWC
        mock_write_rpl.assert_called_once()
        assert result == expected_result

    @patch("xrf_explorer.server.stitcher.stitcher.TransposeStateManager")
    @patch("xrf_explorer.server.stitcher.stitcher.transpose_spectral_datacube")
    @patch.object(SpectralDatacubeFragment, "write_rpl_file")
    @patch.object(SpectralDatacubeFragment, "from_file")
    @patch("os.path.exists")
    @patch("os.remove")
    @patch("numpy.memmap")
    def test_spectral_stitching_with_completed_pretranspose(
        self,
        mock_memmap,
        mock_remove,
        mock_exists,
        mock_from_file,
        mock_write_rpl,
        mock_transpose,
        mock_state_manager_class,
        mock_spectral_fragment,
        mock_warp_selection_pair,
        tmp_path,
    ):
        """Should use pre-transposed file when available."""
        # Setup state manager mock
        mock_state_manager = Mock()
        mock_state_manager_class.get_instance.return_value = mock_state_manager

        completed_status = TransposeInfo(
            status=TransposeState.COMPLETED,
            transposed_path="/path/to/pretransposed.raw",
        )
        mock_state_manager.get_status.return_value = completed_status
        mock_state_manager.cleanup = Mock()

        mock_exists.return_value = False
        mock_memmap.return_value = MagicMock()
        mock_memmap.return_value.__getitem__ = Mock(
            return_value=np.zeros((100, 100), dtype=np.uint16)
        )
        mock_memmap.return_value.__setitem__ = Mock()
        mock_memmap.return_value.flush = Mock()

        expected_result = Mock(spec=SpectralDatacubeFragment)
        mock_from_file.return_value = expected_result

        mock_spectral_fragment.datacube_file = "/path/to/spectral.raw"

        stitcher = DatacubeStitcher(
            fragments=[mock_spectral_fragment],
            intensity_scales=[1.0],
            points=[mock_warp_selection_pair],
            frame=Dimensions(100, 100),
            outputdir=str(tmp_path),
            data_source="test_source",
        )

        with patch.object(stitcher, "fill_layers"):
            result = stitcher.stitch_datacubes()

        mock_state_manager.get_status.assert_called()
        # Should not call create_transposed_version since pre-transpose exists
        mock_spectral_fragment.create_transposed_version.assert_not_called()
        mock_state_manager.cleanup.assert_called_once_with("test_source")

    @patch("xrf_explorer.server.stitcher.stitcher.TransposeStateManager")
    @patch("xrf_explorer.server.stitcher.stitcher.transpose_spectral_datacube")
    @patch.object(SpectralDatacubeFragment, "write_rpl_file")
    @patch.object(SpectralDatacubeFragment, "from_file")
    @patch("os.path.exists")
    @patch("os.remove")
    @patch("numpy.memmap")
    def test_spectral_stitching_waits_for_in_progress_pretranspose(
        self,
        mock_memmap,
        mock_remove,
        mock_exists,
        mock_from_file,
        mock_write_rpl,
        mock_transpose,
        mock_state_manager_class,
        mock_spectral_fragment,
        mock_warp_selection_pair,
        tmp_path,
    ):
        """Should wait for in-progress pre-transpose to complete."""
        mock_state_manager = Mock()
        mock_state_manager_class.get_instance.return_value = mock_state_manager

        in_progress_status = TransposeInfo(status=TransposeState.IN_PROGRESS)
        completed_status = TransposeInfo(
            status=TransposeState.COMPLETED,
            transposed_path="/path/to/pretransposed.raw",
        )
        mock_state_manager.get_status.return_value = in_progress_status
        mock_state_manager.wait_for_completion.return_value = completed_status
        mock_state_manager.cleanup = Mock()

        mock_exists.return_value = False
        mock_memmap.return_value = MagicMock()
        mock_memmap.return_value.flush = Mock()

        expected_result = Mock(spec=SpectralDatacubeFragment)
        mock_from_file.return_value = expected_result

        mock_spectral_fragment.datacube_file = "/path/to/spectral.raw"

        stitcher = DatacubeStitcher(
            fragments=[mock_spectral_fragment],
            intensity_scales=[1.0],
            points=[mock_warp_selection_pair],
            frame=Dimensions(100, 100),
            outputdir=str(tmp_path),
            data_source="test_source",
        )

        with patch.object(stitcher, "fill_layers"):
            stitcher.stitch_datacubes()

        mock_state_manager.wait_for_completion.assert_called_once_with(
            "test_source", "spectral.raw", timeout=None
        )

    @patch("xrf_explorer.server.stitcher.stitcher.TransposeStateManager")
    @patch("xrf_explorer.server.stitcher.stitcher.transpose_spectral_datacube")
    @patch.object(SpectralDatacubeFragment, "write_rpl_file")
    @patch.object(SpectralDatacubeFragment, "from_file")
    @patch("os.path.exists")
    @patch("os.remove")
    @patch("numpy.memmap")
    def test_spectral_stitching_queued_pretranspose(
        self,
        mock_memmap,
        mock_remove,
        mock_exists,
        mock_from_file,
        mock_write_rpl,
        mock_transpose,
        mock_state_manager_class,
        mock_spectral_fragment,
        mock_warp_selection_pair,
        tmp_path,
    ):
        """Should wait for queued pre-transpose to complete."""
        mock_state_manager = Mock()
        mock_state_manager_class.get_instance.return_value = mock_state_manager

        queued_status = TransposeInfo(status=TransposeState.QUEUED)
        completed_status = TransposeInfo(
            status=TransposeState.COMPLETED,
            transposed_path="/path/to/pretransposed.raw",
        )
        mock_state_manager.get_status.return_value = queued_status
        mock_state_manager.wait_for_completion.return_value = completed_status
        mock_state_manager.cleanup = Mock()

        mock_exists.return_value = False
        mock_memmap.return_value = MagicMock()
        mock_memmap.return_value.flush = Mock()

        expected_result = Mock(spec=SpectralDatacubeFragment)
        mock_from_file.return_value = expected_result

        mock_spectral_fragment.datacube_file = "/path/to/spectral.raw"

        stitcher = DatacubeStitcher(
            fragments=[mock_spectral_fragment],
            intensity_scales=[1.0],
            points=[mock_warp_selection_pair],
            frame=Dimensions(100, 100),
            outputdir=str(tmp_path),
            data_source="test_source",
        )

        with patch.object(stitcher, "fill_layers"):
            stitcher.stitch_datacubes()

        mock_state_manager.wait_for_completion.assert_called_once()

    @patch("xrf_explorer.server.stitcher.stitcher.TransposeStateManager")
    @patch("xrf_explorer.server.stitcher.stitcher.transpose_spectral_datacube")
    @patch.object(SpectralDatacubeFragment, "write_rpl_file")
    @patch.object(SpectralDatacubeFragment, "from_file")
    @patch("os.path.exists")
    @patch("os.remove")
    @patch("numpy.memmap")
    def test_spectral_stitching_failed_pretranspose_falls_through(
        self,
        mock_memmap,
        mock_remove,
        mock_exists,
        mock_from_file,
        mock_write_rpl,
        mock_transpose,
        mock_state_manager_class,
        mock_spectral_fragment,
        mock_warp_selection_pair,
        tmp_path,
    ):
        """Should transpose now if pre-transpose failed."""
        mock_state_manager = Mock()
        mock_state_manager_class.get_instance.return_value = mock_state_manager

        failed_status = TransposeInfo(
            status=TransposeState.FAILED, error="IO Error"
        )
        mock_state_manager.get_status.return_value = failed_status
        mock_state_manager.cleanup = Mock()

        mock_exists.return_value = False
        mock_memmap.return_value = MagicMock()
        mock_memmap.return_value.flush = Mock()

        transposed_frag = Mock(spec=SpectralDatacubeFragment)
        transposed_frag.datacube_file = "/path/to/transposed.raw"
        transposed_frag.is_transposed = True
        transposed_frag.load_datacube = Mock(
            return_value=np.ones((100, 50, 50), dtype=np.uint16)
        )
        transposed_frag.rotation = 0
        mock_spectral_fragment.create_transposed_version = Mock(
            return_value=transposed_frag
        )

        expected_result = Mock(spec=SpectralDatacubeFragment)
        mock_from_file.return_value = expected_result

        mock_spectral_fragment.datacube_file = "/path/to/spectral.raw"

        stitcher = DatacubeStitcher(
            fragments=[mock_spectral_fragment],
            intensity_scales=[1.0],
            points=[mock_warp_selection_pair],
            frame=Dimensions(100, 100),
            outputdir=str(tmp_path),
            data_source="test_source",
        )

        with patch.object(stitcher, "fill_layers"):
            stitcher.stitch_datacubes()

        # Should fall through to create_transposed_version
        mock_spectral_fragment.create_transposed_version.assert_called_once()

    @patch("xrf_explorer.server.stitcher.stitcher.transpose_spectral_datacube")
    @patch.object(SpectralDatacubeFragment, "write_rpl_file")
    @patch.object(SpectralDatacubeFragment, "from_file")
    @patch("os.path.exists")
    @patch("os.remove")
    @patch("numpy.memmap")
    def test_spectral_stitching_cleanup_temp_files(
        self,
        mock_memmap,
        mock_remove,
        mock_exists,
        mock_from_file,
        mock_write_rpl,
        mock_transpose,
        mock_spectral_fragment,
        mock_warp_selection_pair,
        tmp_path,
    ):
        """Should clean up temporary transposed files after stitching."""
        mock_exists.return_value = True
        mock_memmap.return_value = MagicMock()
        mock_memmap.return_value.flush = Mock()

        transposed_frag = Mock(spec=SpectralDatacubeFragment)
        transposed_frag.datacube_file = "/path/to/transposed.raw"
        transposed_frag.is_transposed = True
        transposed_frag.load_datacube = Mock(
            return_value=np.ones((100, 50, 50), dtype=np.uint16)
        )
        transposed_frag.rotation = 0
        mock_spectral_fragment.create_transposed_version = Mock(
            return_value=transposed_frag
        )

        expected_result = Mock(spec=SpectralDatacubeFragment)
        mock_from_file.return_value = expected_result

        stitcher = DatacubeStitcher(
            fragments=[mock_spectral_fragment],
            intensity_scales=[1.0],
            points=[mock_warp_selection_pair],
            frame=Dimensions(100, 100),
            outputdir=str(tmp_path),
        )

        with patch.object(stitcher, "fill_layers"):
            stitcher.stitch_datacubes()

        # Should attempt to remove temp files
        assert mock_remove.called

    @patch("xrf_explorer.server.stitcher.stitcher.transpose_spectral_datacube")
    @patch.object(SpectralDatacubeFragment, "write_rpl_file")
    @patch.object(SpectralDatacubeFragment, "from_file")
    @patch("os.path.exists")
    @patch("os.remove")
    @patch("numpy.memmap")
    def test_spectral_stitching_restores_original_fragments(
        self,
        mock_memmap,
        mock_remove,
        mock_exists,
        mock_from_file,
        mock_write_rpl,
        mock_transpose,
        mock_spectral_fragment,
        mock_warp_selection_pair,
        tmp_path,
    ):
        """Should restore original fragments after stitching."""
        mock_exists.return_value = False
        mock_memmap.return_value = MagicMock()
        mock_memmap.return_value.flush = Mock()

        transposed_frag = Mock(spec=SpectralDatacubeFragment)
        transposed_frag.datacube_file = "/path/to/transposed.raw"
        transposed_frag.is_transposed = True
        transposed_frag.load_datacube = Mock(
            return_value=np.ones((100, 50, 50), dtype=np.uint16)
        )
        transposed_frag.rotation = 0
        mock_spectral_fragment.create_transposed_version = Mock(
            return_value=transposed_frag
        )

        expected_result = Mock(spec=SpectralDatacubeFragment)
        mock_from_file.return_value = expected_result

        original_fragments = [mock_spectral_fragment]
        stitcher = DatacubeStitcher(
            fragments=original_fragments,
            intensity_scales=[1.0],
            points=[mock_warp_selection_pair],
            frame=Dimensions(100, 100),
            outputdir=str(tmp_path),
        )

        with patch.object(stitcher, "fill_layers"):
            stitcher.stitch_datacubes()

        # Fragments should be restored to original
        assert stitcher.fragments == original_fragments


class TestGetPerspectiveMatrices:
    """Tests for DatacubeStitcher.get_perspective_matrices"""

    def test_returns_correct_number_of_matrices(
        self, mock_elemental_fragment, mock_warp_selection_pair
    ):
        """Should return one matrix per fragment."""
        stitcher = DatacubeStitcher(
            fragments=[mock_elemental_fragment, mock_elemental_fragment],
            intensity_scales=[1.0, 1.0],
            points=[mock_warp_selection_pair, mock_warp_selection_pair],
            frame=Dimensions(100, 100),
        )

        matrices = stitcher.get_perspective_matrices()

        assert len(matrices) == 2
        assert all(matrix.shape == (3, 3) for matrix in matrices)

    def test_applies_scalar_to_destination_points(self):
        """Should apply scalar when getting destination points."""
        fragment = Mock(spec=DatacubeFragment)
        fragment.are_compatible = Mock(return_value=True)
        fragment.channels = 10

        src = Mock(spec=WarpSelection)
        src.get_points = Mock(
            return_value=np.array(
                [[0, 0], [50, 0], [50, 50], [0, 50]], dtype=np.float32
            )
        )
        dst = Mock(spec=WarpSelection)
        dst.get_points = Mock(
            return_value=np.array(
                [[0, 0], [100, 0], [100, 100], [0, 100]], dtype=np.float32
            )
        )

        stitcher = DatacubeStitcher(
            fragments=[fragment],
            intensity_scales=[1.0],
            points=[(src, dst)],
            frame=Dimensions(200, 200),
            scalar=2.0,
        )

        # Verify dst.get_points was called with scalar
        dst.get_points.assert_called_with(2.0)

    def test_matrices_are_valid_transforms(
        self, mock_elemental_fragment
    ):
        """Should produce valid perspective transform matrices."""
        src = Mock(spec=WarpSelection)
        src.get_points = Mock(
            return_value=np.array(
                [[0, 0], [100, 0], [100, 100], [0, 100]], dtype=np.float32
            )
        )
        dst = Mock(spec=WarpSelection)
        dst.get_points = Mock(
            return_value=np.array(
                [[10, 10], [90, 15], [85, 90], [15, 85]], dtype=np.float32
            )
        )

        stitcher = DatacubeStitcher(
            fragments=[mock_elemental_fragment],
            intensity_scales=[1.0],
            points=[(src, dst)],
            frame=Dimensions(100, 100),
        )

        matrices = stitcher.get_perspective_matrices()

        # Matrix should be 3x3 homogeneous transform
        assert matrices[0].shape == (3, 3)
        # Bottom-right element should be 1 (normalized)
        assert np.isclose(matrices[0][2, 2], 1.0)