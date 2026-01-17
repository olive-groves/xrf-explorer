"""Unit tests for stitch_jobs.py - background job management for stitching."""

import threading
from unittest.mock import MagicMock, patch

import pytest

from xrf_explorer.server.stitcher import stitch_jobs
from xrf_explorer.server.stitcher.stitch_jobs import (
    _run_stitch_job,
    start_stitch_job,
    get_stitch_job_status,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def reset_stitch_jobs():
    """Reset the global _stitch_jobs dict before and after each test."""
    with stitch_jobs._stitch_jobs_lock:
        stitch_jobs._stitch_jobs.clear()
    yield
    with stitch_jobs._stitch_jobs_lock:
        stitch_jobs._stitch_jobs.clear()


@pytest.fixture
def mock_stitch_config():
    """Create a mock StitchData configuration."""
    return MagicMock()


# =============================================================================
# Test _run_stitch_job
# =============================================================================


class TestRunStitchJob:
    def test_successful_stitch(self, mock_stitch_config):
        """Test successful stitch operation updates job to completed."""
        job_id = "test-job-123"
        expected_result = {"status": "success", "output": "stitched.raw"}

        # Pre-populate job entry (as start_stitch_job would do)
        with stitch_jobs._stitch_jobs_lock:
            stitch_jobs._stitch_jobs[job_id] = {
                "status": "in_progress",
                "data_source": "src",
                "result": None,
                "error": None,
            }

        with patch(
            "xrf_explorer.server.stitcher.stitch_jobs.stitch",
            return_value=expected_result,
        ) as mock_stitch:
            _run_stitch_job(job_id, mock_stitch_config)

            mock_stitch.assert_called_once_with(mock_stitch_config)

        # Verify job status updated
        with stitch_jobs._stitch_jobs_lock:
            job = stitch_jobs._stitch_jobs[job_id]

        assert job["status"] == "completed"
        assert job["result"] == expected_result
        assert job["error"] is None

    def test_file_not_found_error(self, mock_stitch_config):
        """Test FileNotFoundError sets status to failed with not_found type."""
        job_id = "test-job-fnf"

        with stitch_jobs._stitch_jobs_lock:
            stitch_jobs._stitch_jobs[job_id] = {
                "status": "in_progress",
                "data_source": "src",
                "result": None,
                "error": None,
            }

        with patch(
            "xrf_explorer.server.stitcher.stitch_jobs.stitch",
            side_effect=FileNotFoundError("missing.raw"),
        ):
            _run_stitch_job(job_id, mock_stitch_config)

        with stitch_jobs._stitch_jobs_lock:
            job = stitch_jobs._stitch_jobs[job_id]

        assert job["status"] == "failed"
        assert "File not found" in job["error"]
        assert "missing.raw" in job["error"]
        assert job["error_type"] == "not_found"

    def test_value_error(self, mock_stitch_config):
        """Test ValueError sets status to failed with validation type."""
        job_id = "test-job-val"

        with stitch_jobs._stitch_jobs_lock:
            stitch_jobs._stitch_jobs[job_id] = {
                "status": "in_progress",
                "data_source": "src",
                "result": None,
                "error": None,
            }

        with patch(
            "xrf_explorer.server.stitcher.stitch_jobs.stitch",
            side_effect=ValueError("Invalid dimensions"),
        ):
            _run_stitch_job(job_id, mock_stitch_config)

        with stitch_jobs._stitch_jobs_lock:
            job = stitch_jobs._stitch_jobs[job_id]

        assert job["status"] == "failed"
        assert "Validation error" in job["error"]
        assert "Invalid dimensions" in job["error"]
        assert job["error_type"] == "validation"

    def test_generic_exception(self, mock_stitch_config):
        """Test generic Exception sets status to failed with internal type."""
        job_id = "test-job-exc"

        with stitch_jobs._stitch_jobs_lock:
            stitch_jobs._stitch_jobs[job_id] = {
                "status": "in_progress",
                "data_source": "src",
                "result": None,
                "error": None,
            }

        with patch(
            "xrf_explorer.server.stitcher.stitch_jobs.stitch",
            side_effect=RuntimeError("Unexpected failure"),
        ):
            _run_stitch_job(job_id, mock_stitch_config)

        with stitch_jobs._stitch_jobs_lock:
            job = stitch_jobs._stitch_jobs[job_id]

        assert job["status"] == "failed"
        assert "Stitching failed" in job["error"]
        assert "Unexpected failure" in job["error"]
        assert job["error_type"] == "internal"


# =============================================================================
# Test start_stitch_job
# =============================================================================


class TestStartStitchJob:
    @patch("xrf_explorer.server.stitcher.stitch_jobs.threading.Thread")
    @patch("xrf_explorer.server.stitcher.stitch_jobs.uuid.uuid4")
    def test_start_stitch_job_creates_job(
        self, mock_uuid, mock_thread_class, mock_stitch_config
    ):
        """Test that start_stitch_job creates job entry and starts thread."""
        mock_uuid.return_value = "fixed-uuid-1234"
        mock_thread_instance = MagicMock()
        mock_thread_class.return_value = mock_thread_instance

        result = start_stitch_job(mock_stitch_config, "test_source")

        # Verify UUID was used
        assert result == "fixed-uuid-1234"

        # Verify job was created with correct initial state
        with stitch_jobs._stitch_jobs_lock:
            job = stitch_jobs._stitch_jobs["fixed-uuid-1234"]

        assert job["status"] == "in_progress"
        assert job["data_source"] == "test_source"
        assert job["result"] is None
        assert job["error"] is None

        # Verify thread was created correctly
        mock_thread_class.assert_called_once_with(
            target=_run_stitch_job,
            args=("fixed-uuid-1234", mock_stitch_config),
            daemon=True,
        )
        mock_thread_instance.start.assert_called_once()

    @patch("xrf_explorer.server.stitcher.stitch_jobs.threading.Thread")
    @patch("xrf_explorer.server.stitcher.stitch_jobs.uuid.uuid4")
    def test_start_stitch_job_returns_unique_ids(
        self, mock_uuid, mock_thread_class, mock_stitch_config
    ):
        """Test that multiple jobs get different IDs."""
        mock_uuid.side_effect = ["uuid-1", "uuid-2"]
        mock_thread_class.return_value = MagicMock()

        id1 = start_stitch_job(mock_stitch_config, "src1")
        id2 = start_stitch_job(mock_stitch_config, "src2")

        assert id1 == "uuid-1"
        assert id2 == "uuid-2"
        assert id1 != id2

        # Both jobs should exist
        with stitch_jobs._stitch_jobs_lock:
            assert "uuid-1" in stitch_jobs._stitch_jobs
            assert "uuid-2" in stitch_jobs._stitch_jobs


# =============================================================================
# Test get_stitch_job_status
# =============================================================================


class TestGetStitchJobStatus:
    def test_job_not_found_returns_none(self):
        """Test that non-existent job ID returns None."""
        result = get_stitch_job_status("nonexistent-id", "any_source")
        assert result is None

    def test_wrong_data_source_returns_none(self):
        """Test that mismatched data_source returns None."""
        job_id = "test-job-ds"

        with stitch_jobs._stitch_jobs_lock:
            stitch_jobs._stitch_jobs[job_id] = {
                "status": "in_progress",
                "data_source": "correct_source",
                "result": None,
                "error": None,
            }

        result = get_stitch_job_status(job_id, "wrong_source")
        assert result is None

    def test_in_progress_job_status(self):
        """Test status dict for in_progress job."""
        job_id = "test-job-ip"

        with stitch_jobs._stitch_jobs_lock:
            stitch_jobs._stitch_jobs[job_id] = {
                "status": "in_progress",
                "data_source": "src",
                "result": None,
                "error": None,
            }

        result = get_stitch_job_status(job_id, "src")

        assert result["job_id"] == job_id
        assert result["status"] == "in_progress"
        assert result["result"] is None
        assert result["error"] is None

    def test_completed_job_status(self):
        """Test status dict for completed job includes result."""
        job_id = "test-job-done"
        expected_result = {"output": "stitched.raw", "dimensions": {"w": 100, "h": 100}}

        with stitch_jobs._stitch_jobs_lock:
            stitch_jobs._stitch_jobs[job_id] = {
                "status": "completed",
                "data_source": "src",
                "result": expected_result,
                "error": None,
            }

        result = get_stitch_job_status(job_id, "src")

        assert result["job_id"] == job_id
        assert result["status"] == "completed"
        assert result["result"] == expected_result
        assert result["error"] is None

    def test_failed_job_status(self):
        """Test status dict for failed job includes error."""
        job_id = "test-job-fail"

        with stitch_jobs._stitch_jobs_lock:
            stitch_jobs._stitch_jobs[job_id] = {
                "status": "failed",
                "data_source": "src",
                "result": None,
                "error": "Something went wrong",
            }

        result = get_stitch_job_status(job_id, "src")

        assert result["job_id"] == job_id
        assert result["status"] == "failed"
        assert result["result"] is None
        assert result["error"] == "Something went wrong"

    def test_completed_job_does_not_return_error(self):
        """Test that completed job returns result, not error field content."""
        job_id = "test-job-edge"

        # Edge case: job has both result and error set (shouldn't happen, but test behavior)
        with stitch_jobs._stitch_jobs_lock:
            stitch_jobs._stitch_jobs[job_id] = {
                "status": "completed",
                "data_source": "src",
                "result": {"data": "value"},
                "error": "stale error",  # shouldn't be returned
            }

        result = get_stitch_job_status(job_id, "src")

        assert result["status"] == "completed"
        assert result["result"] == {"data": "value"}
        assert result["error"] is None  # Error not returned for completed

    def test_failed_job_does_not_return_result(self):
        """Test that failed job returns error, not result field content."""
        job_id = "test-job-edge2"

        with stitch_jobs._stitch_jobs_lock:
            stitch_jobs._stitch_jobs[job_id] = {
                "status": "failed",
                "data_source": "src",
                "result": {"stale": "data"},  # shouldn't be returned
                "error": "actual error",
            }

        result = get_stitch_job_status(job_id, "src")

        assert result["status"] == "failed"
        assert result["result"] is None  # Result not returned for failed
        assert result["error"] == "actual error"