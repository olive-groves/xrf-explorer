"""
Unit tests for xrf_explorer.server.stitcher.transpose_state module.

Tests cover the TransposeState enum, TransposeInfo dataclass, TransposeJob dataclass,
and the TransposeStateManager singleton class with 100% coverage.
"""
from __future__ import annotations

import time
from datetime import datetime
from threading import Thread, Event
from unittest.mock import MagicMock, patch

import pytest

from xrf_explorer.server.stitcher.transpose_state import (
    TransposeState,
    TransposeInfo,
    TransposeJob,
    TransposeStateManager,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def reset_singleton():
    """Reset the TransposeStateManager singleton before and after each test."""
    # Reset before test
    TransposeStateManager._instance = None

    yield

    # Reset after test - stop worker thread if running
    if TransposeStateManager._instance is not None:
        instance = TransposeStateManager._instance
        instance._running = False
        if hasattr(instance, "_worker_thread") and instance._worker_thread.is_alive():
            instance._worker_thread.join(timeout=2.0)
        TransposeStateManager._instance = None


@pytest.fixture
def manager(reset_singleton):
    """Provide a fresh TransposeStateManager instance for testing."""
    return TransposeStateManager.get_instance()


# =============================================================================
# Test TransposeState Enum
# =============================================================================


class TestTransposeState:
    def test_enum_values(self):
        """Test that all enum values exist with correct string representations."""
        assert TransposeState.NOT_STARTED.value == "not_started"
        assert TransposeState.QUEUED.value == "queued"
        assert TransposeState.IN_PROGRESS.value == "in_progress"
        assert TransposeState.COMPLETED.value == "completed"
        assert TransposeState.FAILED.value == "failed"


# =============================================================================
# Test TransposeInfo Dataclass
# =============================================================================


class TestTransposeInfo:
    def test_default_initialization(self):
        """Test default values on initialization."""
        info = TransposeInfo()

        assert info.status == TransposeState.NOT_STARTED
        assert info.transposed_path is None
        assert info.error is None
        assert info.started_at is None
        assert info.completed_at is None

    def test_custom_initialization(self):
        """Test initialization with custom values."""
        now = datetime.now()
        info = TransposeInfo(
            status=TransposeState.COMPLETED,
            transposed_path="/path/to/file.raw",
            error=None,
            started_at=now,
            completed_at=now,
        )

        assert info.status == TransposeState.COMPLETED
        assert info.transposed_path == "/path/to/file.raw"
        assert info.started_at == now
        assert info.completed_at == now

    def test_to_dict_with_none_values(self):
        """Test to_dict() when all optional fields are None."""
        info = TransposeInfo()
        result = info.to_dict()

        assert result == {
            "status": "not_started",
            "transposed_path": None,
            "error": None,
            "started_at": None,
            "completed_at": None,
        }

    def test_to_dict_with_all_values(self):
        """Test to_dict() when all fields are populated."""
        started = datetime(2026, 1, 17, 10, 0, 0)
        completed = datetime(2026, 1, 17, 10, 5, 0)

        info = TransposeInfo(
            status=TransposeState.COMPLETED,
            transposed_path="/output/transposed.raw",
            error=None,
            started_at=started,
            completed_at=completed,
        )
        result = info.to_dict()

        assert result["status"] == "completed"
        assert result["transposed_path"] == "/output/transposed.raw"
        assert result["error"] is None
        assert result["started_at"] == "2026-01-17T10:00:00"
        assert result["completed_at"] == "2026-01-17T10:05:00"

    def test_to_dict_with_error(self):
        """Test to_dict() for a failed transpose."""
        started = datetime(2026, 1, 17, 10, 0, 0)
        completed = datetime(2026, 1, 17, 10, 1, 0)

        info = TransposeInfo(
            status=TransposeState.FAILED,
            transposed_path=None,
            error="File not found",
            started_at=started,
            completed_at=completed,
        )
        result = info.to_dict()

        assert result["status"] == "failed"
        assert result["transposed_path"] is None
        assert result["error"] == "File not found"


# =============================================================================
# Test TransposeJob Dataclass
# =============================================================================


class TestTransposeJob:
    def test_initialization(self):
        """Test TransposeJob can be instantiated with required attributes."""
        worker_fn = MagicMock()
        job = TransposeJob(
            data_source="source1",
            cube_file="cube.raw",
            worker_func=worker_fn,
        )

        assert job.data_source == "source1"
        assert job.cube_file == "cube.raw"
        assert job.worker_func is worker_fn


# =============================================================================
# Test TransposeStateManager Singleton
# =============================================================================


class TestTransposeStateManagerSingleton:
    def test_singleton_returns_same_instance(self, reset_singleton):
        """Test that multiple instantiations return the same object."""
        instance1 = TransposeStateManager()
        instance2 = TransposeStateManager()

        assert instance1 is instance2

    def test_get_instance_returns_singleton(self, reset_singleton):
        """Test get_instance() returns the singleton."""
        instance1 = TransposeStateManager.get_instance()
        instance2 = TransposeStateManager.get_instance()

        assert instance1 is instance2

    def test_init_only_runs_once(self, reset_singleton):
        """Test that __init__ only initializes once."""
        instance1 = TransposeStateManager()
        original_states = instance1._states

        # Add some state
        instance1._states["test"] = {}

        # Create another "instance"
        instance2 = TransposeStateManager()

        # States should still contain our modification
        assert "test" in instance2._states
        assert instance2._states is original_states


# =============================================================================
# Test TransposeStateManager._get_condition
# =============================================================================


class TestGetCondition:
    def test_creates_condition_for_new_data_source(self, manager):
        """Test that _get_condition creates new structures for unknown data source."""
        condition = manager._get_condition("new_source", "cube.raw")

        assert condition is not None
        assert "new_source" in manager._conditions
        assert "cube.raw" in manager._conditions["new_source"]

    def test_creates_condition_for_new_cube(self, manager):
        """Test creating condition for new cube in existing data source."""
        manager._get_condition("source", "cube1.raw")
        condition2 = manager._get_condition("source", "cube2.raw")

        assert condition2 is not None
        assert "cube1.raw" in manager._conditions["source"]
        assert "cube2.raw" in manager._conditions["source"]

    def test_returns_existing_condition(self, manager):
        """Test that same condition is returned for same cube."""
        condition1 = manager._get_condition("source", "cube.raw")
        condition2 = manager._get_condition("source", "cube.raw")

        assert condition1 is condition2


# =============================================================================
# Test TransposeStateManager.enqueue_transpose
# =============================================================================


class TestEnqueueTranspose:
    def test_successful_enqueue(self, manager):
        """Test successfully enqueueing a new transpose job."""
        worker = MagicMock()

        result = manager.enqueue_transpose("source", "cube.raw", worker)

        assert result is True
        assert manager._states["source"]["cube.raw"].status == TransposeState.QUEUED

    def test_enqueue_creates_data_source(self, manager):
        """Test that enqueue creates data source entry if not exists."""
        worker = MagicMock()

        manager.enqueue_transpose("new_source", "cube.raw", worker)

        assert "new_source" in manager._states

    def test_enqueue_when_already_queued(self, manager):
        """Test that enqueue returns False when already QUEUED."""
        worker = MagicMock()

        manager.enqueue_transpose("source", "cube.raw", worker)
        result = manager.enqueue_transpose("source", "cube.raw", worker)

        assert result is False

    def test_enqueue_when_in_progress(self, manager):
        """Test that enqueue returns False when IN_PROGRESS."""
        manager._states["source"] = {
            "cube.raw": TransposeInfo(status=TransposeState.IN_PROGRESS)
        }
        worker = MagicMock()

        result = manager.enqueue_transpose("source", "cube.raw", worker)

        assert result is False

    def test_enqueue_when_completed(self, manager):
        """Test that enqueue returns False when already COMPLETED."""
        manager._states["source"] = {
            "cube.raw": TransposeInfo(status=TransposeState.COMPLETED)
        }
        worker = MagicMock()

        result = manager.enqueue_transpose("source", "cube.raw", worker)

        assert result is False

    def test_enqueue_when_failed_allows_retry(self, manager):
        """Test that enqueue allows retry after FAILED state."""
        manager._states["source"] = {
            "cube.raw": TransposeInfo(status=TransposeState.FAILED, error="prev error")
        }
        worker = MagicMock()

        result = manager.enqueue_transpose("source", "cube.raw", worker)

        assert result is True
        assert manager._states["source"]["cube.raw"].status == TransposeState.QUEUED


# =============================================================================
# Test TransposeStateManager.start_transpose
# =============================================================================


class TestStartTranspose:
    def test_start_new_transpose(self, manager):
        """Test starting transpose for a new cube."""
        result = manager.start_transpose("source", "cube.raw")

        assert result is True
        info = manager._states["source"]["cube.raw"]
        assert info.status == TransposeState.IN_PROGRESS
        assert info.started_at is not None

    def test_start_creates_data_source(self, manager):
        """Test that start_transpose creates data source if needed."""
        manager.start_transpose("new_source", "cube.raw")

        assert "new_source" in manager._states

    def test_start_when_already_in_progress(self, manager):
        """Test that start returns False when already IN_PROGRESS."""
        manager._states["source"] = {
            "cube.raw": TransposeInfo(status=TransposeState.IN_PROGRESS)
        }

        result = manager.start_transpose("source", "cube.raw")

        assert result is False

    def test_start_when_already_completed(self, manager):
        """Test that start returns False when already COMPLETED."""
        manager._states["source"] = {
            "cube.raw": TransposeInfo(status=TransposeState.COMPLETED)
        }

        result = manager.start_transpose("source", "cube.raw")

        assert result is False

    def test_start_after_queued(self, manager):
        """Test starting transpose that was queued."""
        manager._states["source"] = {
            "cube.raw": TransposeInfo(status=TransposeState.QUEUED)
        }

        result = manager.start_transpose("source", "cube.raw")

        assert result is True
        assert manager._states["source"]["cube.raw"].status == TransposeState.IN_PROGRESS


# =============================================================================
# Test TransposeStateManager.complete_transpose
# =============================================================================


class TestCompleteTranspose:
    def test_complete_success(self, manager):
        """Test successful completion with transposed path."""
        manager.start_transpose("source", "cube.raw")

        manager.complete_transpose(
            "source", "cube.raw", transposed_path="/output/transposed.raw"
        )

        info = manager._states["source"]["cube.raw"]
        assert info.status == TransposeState.COMPLETED
        assert info.transposed_path == "/output/transposed.raw"
        assert info.error is None
        assert info.completed_at is not None

    def test_complete_failure(self, manager):
        """Test completion with error."""
        manager.start_transpose("source", "cube.raw")

        manager.complete_transpose("source", "cube.raw", error="Disk full")

        info = manager._states["source"]["cube.raw"]
        assert info.status == TransposeState.FAILED
        assert info.error == "Disk full"
        assert info.transposed_path is None
        assert info.completed_at is not None

    def test_complete_creates_state_if_missing(self, manager):
        """Test that complete_transpose creates state entries if needed."""
        manager.complete_transpose(
            "new_source", "new_cube.raw", transposed_path="/path.raw"
        )

        assert "new_source" in manager._states
        assert "new_cube.raw" in manager._states["new_source"]

    def test_complete_notifies_waiting_threads(self, manager):
        """Test that completion notifies threads waiting on condition."""
        manager.start_transpose("source", "cube.raw")
        notified = Event()

        def waiter():
            manager.wait_for_completion("source", "cube.raw", timeout=5.0)
            notified.set()

        thread = Thread(target=waiter)
        thread.start()

        # Give thread time to start waiting
        time.sleep(0.1)

        manager.complete_transpose("source", "cube.raw", transposed_path="/done.raw")

        thread.join(timeout=2.0)
        assert notified.is_set()


# =============================================================================
# Test TransposeStateManager.get_status
# =============================================================================


class TestGetStatus:
    def test_get_status_unknown_data_source(self, manager):
        """Test getting status for unknown data source returns NOT_STARTED."""
        info = manager.get_status("unknown_source", "cube.raw")

        assert info.status == TransposeState.NOT_STARTED

    def test_get_status_unknown_cube(self, manager):
        """Test getting status for unknown cube in known source."""
        manager._states["source"] = {}

        info = manager.get_status("source", "unknown.raw")

        assert info.status == TransposeState.NOT_STARTED

    def test_get_status_known_cube(self, manager):
        """Test getting status for known cube."""
        manager._states["source"] = {
            "cube.raw": TransposeInfo(
                status=TransposeState.COMPLETED, transposed_path="/done.raw"
            )
        }

        info = manager.get_status("source", "cube.raw")

        assert info.status == TransposeState.COMPLETED
        assert info.transposed_path == "/done.raw"


# =============================================================================
# Test TransposeStateManager.get_all_statuses
# =============================================================================


class TestGetAllStatuses:
    def test_get_all_unknown_data_source(self, manager):
        """Test getting all statuses for unknown data source."""
        result = manager.get_all_statuses("unknown")

        assert result == {}

    def test_get_all_with_cubes(self, manager):
        """Test getting all statuses for data source with cubes."""
        manager._states["source"] = {
            "cube1.raw": TransposeInfo(status=TransposeState.COMPLETED),
            "cube2.raw": TransposeInfo(status=TransposeState.IN_PROGRESS),
        }

        result = manager.get_all_statuses("source")

        assert len(result) == 2
        assert "cube1.raw" in result
        assert "cube2.raw" in result

    def test_get_all_returns_copy(self, manager):
        """Test that get_all_statuses returns a copy, not the original."""
        manager._states["source"] = {
            "cube.raw": TransposeInfo(status=TransposeState.COMPLETED)
        }

        result = manager.get_all_statuses("source")
        result["new_cube.raw"] = TransposeInfo()

        # Original should be unmodified
        assert "new_cube.raw" not in manager._states["source"]


# =============================================================================
# Test TransposeStateManager.wait_for_completion
# =============================================================================


class TestWaitForCompletion:
    def test_wait_returns_immediately_for_not_started(self, manager):
        """Test that wait returns immediately for NOT_STARTED state."""
        start = time.time()
        info = manager.wait_for_completion("source", "cube.raw", timeout=5.0)
        elapsed = time.time() - start

        assert info.status == TransposeState.NOT_STARTED
        assert elapsed < 1.0

    def test_wait_returns_immediately_for_completed(self, manager):
        """Test that wait returns immediately for COMPLETED state."""
        manager._states["source"] = {
            "cube.raw": TransposeInfo(status=TransposeState.COMPLETED)
        }

        start = time.time()
        info = manager.wait_for_completion("source", "cube.raw", timeout=5.0)
        elapsed = time.time() - start

        assert info.status == TransposeState.COMPLETED
        assert elapsed < 1.0

    def test_wait_returns_immediately_for_failed(self, manager):
        """Test that wait returns immediately for FAILED state."""
        manager._states["source"] = {
            "cube.raw": TransposeInfo(status=TransposeState.FAILED, error="err")
        }

        info = manager.wait_for_completion("source", "cube.raw", timeout=5.0)

        assert info.status == TransposeState.FAILED

    def test_wait_blocks_for_in_progress(self, manager):
        """Test that wait blocks for IN_PROGRESS until completed."""
        manager._states["source"] = {
            "cube.raw": TransposeInfo(status=TransposeState.IN_PROGRESS)
        }
        completed = Event()

        def completer():
            time.sleep(0.2)
            manager.complete_transpose("source", "cube.raw", transposed_path="/done.raw")
            completed.set()

        thread = Thread(target=completer)
        thread.start()

        info = manager.wait_for_completion("source", "cube.raw", timeout=5.0)

        thread.join()
        assert info.status == TransposeState.COMPLETED
        assert completed.is_set()

    def test_wait_blocks_for_queued(self, manager):
        """Test that wait blocks for QUEUED state."""
        manager._states["source"] = {
            "cube.raw": TransposeInfo(status=TransposeState.QUEUED)
        }

        def completer():
            time.sleep(0.2)
            manager.complete_transpose("source", "cube.raw", transposed_path="/done.raw")

        thread = Thread(target=completer)
        thread.start()

        info = manager.wait_for_completion("source", "cube.raw", timeout=5.0)

        thread.join()
        assert info.status == TransposeState.COMPLETED

    def test_wait_timeout_expires(self, manager):
        """Test that wait returns after timeout expires."""
        manager._states["source"] = {
            "cube.raw": TransposeInfo(status=TransposeState.IN_PROGRESS)
        }

        start = time.time()
        info = manager.wait_for_completion("source", "cube.raw", timeout=0.3)
        elapsed = time.time() - start

        # Should still be in progress after timeout
        assert info.status == TransposeState.IN_PROGRESS
        assert 0.2 < elapsed < 0.6


# =============================================================================
# Test TransposeStateManager.cleanup
# =============================================================================


class TestCleanup:
    def test_cleanup_existing_data_source(self, manager):
        """Test cleaning up an existing data source."""
        manager._states["source"] = {"cube.raw": TransposeInfo()}
        manager._conditions["source"] = {"cube.raw": manager._get_condition("source", "cube.raw")}

        manager.cleanup("source")

        assert "source" not in manager._states
        assert "source" not in manager._conditions

    def test_cleanup_nonexistent_data_source(self, manager):
        """Test cleaning up a non-existent data source doesn't raise."""
        # Should not raise
        manager.cleanup("nonexistent")

    def test_cleanup_only_affects_specified_source(self, manager):
        """Test that cleanup only affects the specified data source."""
        manager._states["source1"] = {"cube.raw": TransposeInfo()}
        manager._states["source2"] = {"cube.raw": TransposeInfo()}

        manager.cleanup("source1")

        assert "source1" not in manager._states
        assert "source2" in manager._states


# =============================================================================
# Test TransposeStateManager.cleanup_cube
# =============================================================================


class TestCleanupCube:
    def test_cleanup_cube_existing(self, manager):
        """Test cleaning up an existing cube."""
        manager._states["source"] = {
            "cube1.raw": TransposeInfo(),
            "cube2.raw": TransposeInfo(),
        }
        manager._get_condition("source", "cube1.raw")

        manager.cleanup_cube("source", "cube1.raw")

        assert "cube1.raw" not in manager._states["source"]
        assert "cube2.raw" in manager._states["source"]

    def test_cleanup_cube_nonexistent(self, manager):
        """Test cleaning up non-existent cube doesn't raise."""
        manager._states["source"] = {}

        # Should not raise
        manager.cleanup_cube("source", "nonexistent.raw")

    def test_cleanup_cube_nonexistent_source(self, manager):
        """Test cleaning up cube from non-existent source doesn't raise."""
        # Should not raise
        manager.cleanup_cube("nonexistent", "cube.raw")


# =============================================================================
# Test TransposeStateManager.is_any_in_progress
# =============================================================================


class TestIsAnyInProgress:
    def test_no_data_source(self, manager):
        """Test is_any_in_progress for non-existent data source."""
        result = manager.is_any_in_progress("nonexistent")

        assert result is False

    def test_no_cubes_in_progress(self, manager):
        """Test when no cubes are in progress."""
        manager._states["source"] = {
            "cube1.raw": TransposeInfo(status=TransposeState.COMPLETED),
            "cube2.raw": TransposeInfo(status=TransposeState.QUEUED),
            "cube3.raw": TransposeInfo(status=TransposeState.FAILED),
        }

        result = manager.is_any_in_progress("source")

        assert result is False

    def test_some_cubes_in_progress(self, manager):
        """Test when some cubes are in progress."""
        manager._states["source"] = {
            "cube1.raw": TransposeInfo(status=TransposeState.COMPLETED),
            "cube2.raw": TransposeInfo(status=TransposeState.IN_PROGRESS),
        }

        result = manager.is_any_in_progress("source")

        assert result is True


# =============================================================================
# Test TransposeStateManager.get_transposed_path
# =============================================================================


class TestGetTransposedPath:
    def test_get_path_completed(self, manager):
        """Test getting path for completed transpose."""
        manager._states["source"] = {
            "cube.raw": TransposeInfo(
                status=TransposeState.COMPLETED, transposed_path="/output/transposed.raw"
            )
        }

        result = manager.get_transposed_path("source", "cube.raw")

        assert result == "/output/transposed.raw"

    def test_get_path_not_completed(self, manager):
        """Test getting path for non-completed transpose."""
        manager._states["source"] = {
            "cube.raw": TransposeInfo(status=TransposeState.IN_PROGRESS)
        }

        result = manager.get_transposed_path("source", "cube.raw")

        assert result is None

    def test_get_path_failed(self, manager):
        """Test getting path for failed transpose."""
        manager._states["source"] = {
            "cube.raw": TransposeInfo(status=TransposeState.FAILED, error="err")
        }

        result = manager.get_transposed_path("source", "cube.raw")

        assert result is None

    def test_get_path_unknown_cube(self, manager):
        """Test getting path for unknown cube."""
        result = manager.get_transposed_path("source", "unknown.raw")

        assert result is None


# =============================================================================
# Test TransposeStateManager._queue_worker
# =============================================================================


class TestQueueWorker:
    def test_worker_processes_job(self, manager):
        """Test that the queue worker processes enqueued jobs."""
        job_executed = Event()

        def worker_fn():
            job_executed.set()
            manager.complete_transpose("source", "cube.raw", transposed_path="/done.raw")

        manager.enqueue_transpose("source", "cube.raw", worker_fn)

        # Wait for job to be processed
        job_executed.wait(timeout=3.0)

        assert job_executed.is_set()
        info = manager.get_status("source", "cube.raw")
        assert info.status == TransposeState.COMPLETED

    def test_worker_handles_exception(self, manager):
        """Test that worker continues after job raises exception."""
        first_executed = Event()
        second_executed = Event()

        def failing_worker():
            first_executed.set()
            raise RuntimeError("Test error")

        def success_worker():
            second_executed.set()
            manager.complete_transpose("source", "cube2.raw", transposed_path="/done.raw")

        manager.enqueue_transpose("source", "cube1.raw", failing_worker)
        manager.enqueue_transpose("source", "cube2.raw", success_worker)

        # Wait for both to be processed
        first_executed.wait(timeout=3.0)
        second_executed.wait(timeout=3.0)

        assert first_executed.is_set()
        assert second_executed.is_set()

    def test_worker_stops_when_running_false(self, reset_singleton):
        """Test that worker thread stops when _running is set to False."""
        manager = TransposeStateManager.get_instance()

        assert manager._worker_thread.is_alive()

        manager._running = False
        manager._worker_thread.join(timeout=3.0)

        assert not manager._worker_thread.is_alive()

    def test_worker_creates_state_for_job(self, manager):
        """Test that worker creates state entry if job has no prior state."""
        executed = Event()

        def worker_fn():
            executed.set()
            manager.complete_transpose("source", "cube.raw", transposed_path="/done.raw")

        # Manually queue a job without using enqueue_transpose
        job = TransposeJob("source", "cube.raw", worker_fn)
        manager._queue.put(job)

        executed.wait(timeout=3.0)

        # Worker should have created the state entry
        info = manager.get_status("source", "cube.raw")
        assert info.status == TransposeState.COMPLETED