"""
Module for managing transpose state across multiple data sources.

This module provides thread-safe state management for pre-transposing spectral datacubes.
It tracks which cubes are being transposed, have been transposed, or haven't started yet.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from logging import Logger, getLogger
from queue import Queue
from threading import Lock, Condition, Thread
from typing import Dict, Optional, Callable

LOG: Logger = getLogger(__name__)


class TransposeState(Enum):
    """Enum representing the state of a transpose operation."""
    NOT_STARTED = "not_started"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TransposeInfo:
    """
    Holds information about a transpose operation.
    
    Attributes:
        status: Current state of the transpose operation.
        transposed_path: Path to the transposed file (set when completed).
        error: Error message if the transpose failed.
        started_at: Timestamp when transpose started.
        completed_at: Timestamp when transpose completed or failed.
    """
    status: TransposeState = TransposeState.NOT_STARTED
    transposed_path: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "status": self.status.value,
            "transposed_path": self.transposed_path,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class TransposeJob:
    """
    Represents a transpose job to be queued.
    
    Attributes:
        data_source: Name of the data source.
        cube_file: Name of the cube file.
        worker_func: Function to execute for the transpose.
    """
    data_source: str
    cube_file: str
    worker_func: Callable[[], None]


class TransposeStateManager:
    """
    Singleton class for managing transpose state across multiple data sources.
    
    This class provides thread-safe operations for tracking the state of transpose
    operations for spectral datacubes. It supports multiple data sources and 
    multiple cubes per data source.
    
    Usage:
        manager = TransposeStateManager.get_instance()
        manager.start_transpose("data_source_1", "cube1.raw")
        # ... do transpose work ...
        manager.complete_transpose("data_source_1", "cube1.raw", "/path/to/transposed.raw")
        
        # In another thread:
        state = manager.wait_for_completion("data_source_1", "cube1.raw", timeout=300)
    """
    
    _instance: Optional[TransposeStateManager] = None
    _instance_lock: Lock = Lock()
    
    def __new__(cls) -> TransposeStateManager:
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            with cls._instance_lock:
                # Double-check locking
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the state manager (only runs once due to singleton)."""
        if self._initialized:
            return
            
        # Dictionary structure: {data_source: {cube_file: TransposeInfo}}
        self._states: Dict[str, Dict[str, TransposeInfo]] = {}
        
        # Lock for modifying the states dictionary
        self._lock: Lock = Lock()
        
        # Conditions for each data_source+cube_file combination to enable waiting
        # Structure: {data_source: {cube_file: Condition}}
        self._conditions: Dict[str, Dict[str, Condition]] = {}
        
        # Queue for sequential transpose processing
        self._queue: Queue[TransposeJob] = Queue()
        
        # Flag to control worker thread
        self._running: bool = True
        
        # Start worker thread
        self._worker_thread = Thread(
            target=self._queue_worker,
            name="transpose-queue-worker",
            daemon=True
        )
        self._worker_thread.start()
        
        self._initialized = True
        LOG.info("TransposeStateManager initialized with queue worker")
    
    @classmethod
    def get_instance(cls) -> TransposeStateManager:
        """Get the singleton instance of TransposeStateManager."""
        return cls()
    
    def _get_condition(self, data_source: str, cube_file: str) -> Condition:
        """Get or create a condition variable for a specific cube."""
        with self._lock:
            if data_source not in self._conditions:
                self._conditions[data_source] = {}
            if cube_file not in self._conditions[data_source]:
                self._conditions[data_source][cube_file] = Condition()
            return self._conditions[data_source][cube_file]
    
    def _queue_worker(self) -> None:
        """
        Worker thread that processes transpose jobs from the queue sequentially.
        
        This ensures that only one transpose operation runs at a time,
        preventing system resource overload.
        """
        LOG.info("Transpose queue worker started")
        while self._running:
            try:
                # Wait for a job (blocks until available)
                # Using timeout to allow checking _running flag periodically
                try:
                    job = self._queue.get(timeout=1.0)
                except:
                    # Timeout occurred, check if should continue
                    continue

                # Mark as in progress (should already be marked, but ensure it)
                with self._lock:
                    if job.data_source not in self._states:
                        self._states[job.data_source] = {}
                    if job.cube_file not in self._states[job.data_source]:
                        self._states[job.data_source][job.cube_file] = TransposeInfo(
                            status=TransposeState.IN_PROGRESS,
                            started_at=datetime.now()
                        )
                
                # Execute the transpose work
                job.worker_func()
                
                # Mark as done in queue
                self._queue.task_done()

            except Exception as e:
                LOG.error(f"Error in transpose queue worker: {e}")
        
        LOG.info("Transpose queue worker stopped")
    
    def enqueue_transpose(
        self,
        data_source: str,
        cube_file: str,
        worker_func: Callable[[], None]
    ) -> bool:
        """
        Add a transpose job to the queue for sequential processing.
        
        Args:
            data_source: Name of the data source.
            cube_file: Name/path of the cube file.
            worker_func: Function to execute for the transpose.
            
        Returns:
            True if job was queued, False if already queued/in progress/completed.
        """
        with self._lock:
            if data_source not in self._states:
                self._states[data_source] = {}
            
            current_info = self._states[data_source].get(cube_file)
            
            # Don't enqueue if already queued, in progress, or completed
            if current_info and current_info.status in (
                TransposeState.QUEUED,
                TransposeState.IN_PROGRESS,
                TransposeState.COMPLETED
            ):
                LOG.info(f"Transpose for {data_source}/{cube_file} already {current_info.status.value}")
                return False
            
            # Mark as queued
            self._states[data_source][cube_file] = TransposeInfo(
                status=TransposeState.QUEUED,
                started_at=None  # Will be set when actually starting
            )
            
            # Add to queue
            job = TransposeJob(data_source, cube_file, worker_func)
            self._queue.put(job)
            
            LOG.info(f"Queued transpose for {data_source}/{cube_file}")
            return True
    
    def start_transpose(self, data_source: str, cube_file: str) -> bool:
        """
        Mark a cube as starting transpose (called by worker thread).
        
        Args:
            data_source: Name of the data source.
            cube_file: Name/path of the cube file.
            
        Returns:
            True if transpose was started, False if already in progress or completed.
        """
        with self._lock:
            if data_source not in self._states:
                self._states[data_source] = {}
            
            current_info = self._states[data_source].get(cube_file)
            
            # Don't restart if already in progress or completed
            if current_info and current_info.status in (TransposeState.IN_PROGRESS, TransposeState.COMPLETED):
                LOG.info(f"Transpose for {data_source}/{cube_file} already {current_info.status.value}")
                return False
            
            self._states[data_source][cube_file] = TransposeInfo(
                status=TransposeState.IN_PROGRESS,
                started_at=datetime.now()
            )
            LOG.info(f"Started transpose for {data_source}/{cube_file}")
            return True
    
    def complete_transpose(
        self, 
        data_source: str, 
        cube_file: str, 
        transposed_path: Optional[str] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Mark a cube transpose as completed (success or failure).
        
        Args:
            data_source: Name of the data source.
            cube_file: Name/path of the cube file.
            transposed_path: Path to the transposed file (if successful).
            error: Error message (if failed).
        """
        condition = self._get_condition(data_source, cube_file)
        
        with self._lock:
            if data_source not in self._states:
                self._states[data_source] = {}
            
            info = self._states[data_source].get(cube_file, TransposeInfo())
            info.completed_at = datetime.now()
            
            if error:
                info.status = TransposeState.FAILED
                info.error = error
                LOG.error(f"Transpose failed for {data_source}/{cube_file}: {error}")
            else:
                info.status = TransposeState.COMPLETED
                info.transposed_path = transposed_path
                LOG.info(f"Transpose completed for {data_source}/{cube_file}: {transposed_path}")
            
            self._states[data_source][cube_file] = info
        
        # Notify any waiting threads
        with condition:
            condition.notify_all()
    
    def get_status(self, data_source: str, cube_file: str) -> TransposeInfo:
        """
        Get the current transpose status for a specific cube.
        
        Args:
            data_source: Name of the data source.
            cube_file: Name/path of the cube file.
            
        Returns:
            TransposeInfo with current status.
        """
        with self._lock:
            if data_source not in self._states:
                return TransposeInfo(status=TransposeState.NOT_STARTED)
            return self._states[data_source].get(
                cube_file, 
                TransposeInfo(status=TransposeState.NOT_STARTED)
            )
    
    def get_all_statuses(self, data_source: str) -> Dict[str, TransposeInfo]:
        """
        Get transpose status for all cubes in a data source.
        
        Args:
            data_source: Name of the data source.
            
        Returns:
            Dictionary mapping cube file names to their TransposeInfo.
        """
        with self._lock:
            if data_source not in self._states:
                return {}
            # Return a copy to avoid external modification
            return dict(self._states[data_source])
    
    def wait_for_completion(
        self,
        data_source: str,
        cube_file: str,
        timeout: Optional[float] = None
    ) -> TransposeInfo:
        """
        Wait for a transpose operation to complete.
        
        This method blocks until the transpose is completed (success or failure)
        or the timeout expires. It waits for both QUEUED and IN_PROGRESS states.
        
        Args:
            data_source: Name of the data source.
            cube_file: Name/path of the cube file.
            timeout: Maximum seconds to wait (None = wait forever).
            
        Returns:
            TransposeInfo with final status.
        """
        condition = self._get_condition(data_source, cube_file)
        
        with condition:
            while True:
                info = self.get_status(data_source, cube_file)
                
                # If not started or already done, return immediately
                if info.status in (TransposeState.NOT_STARTED, TransposeState.COMPLETED, TransposeState.FAILED):
                    return info
                
                # Keep waiting if queued or in progress
                if info.status in (TransposeState.QUEUED, TransposeState.IN_PROGRESS):
                    # Wait for notification or timeout
                    if not condition.wait(timeout=timeout):
                        # Timeout expired
                        return self.get_status(data_source, cube_file)
                else:
                    # Unexpected state, return it
                    return info
    
    def cleanup(self, data_source: str) -> None:
        """
        Clean up state for a data source after stitching is complete.
        
        This removes all tracked state for the data source, allowing
        future transpose operations to start fresh.
        
        Args:
            data_source: Name of the data source to clean up.
        """
        with self._lock:
            if data_source in self._states:
                del self._states[data_source]
                LOG.info(f"Cleaned up transpose state for {data_source}")
            if data_source in self._conditions:
                del self._conditions[data_source]
    
    def cleanup_cube(self, data_source: str, cube_file: str) -> None:
        """
        Clean up state for a specific cube.
        
        Args:
            data_source: Name of the data source.
            cube_file: Name/path of the cube file.
        """
        with self._lock:
            if data_source in self._states and cube_file in self._states[data_source]:
                del self._states[data_source][cube_file]
                LOG.info(f"Cleaned up transpose state for {data_source}/{cube_file}")
            if data_source in self._conditions and cube_file in self._conditions[data_source]:
                del self._conditions[data_source][cube_file]
    
    def is_any_in_progress(self, data_source: str) -> bool:
        """
        Check if any transpose operations are in progress for a data source.
        
        Args:
            data_source: Name of the data source.
            
        Returns:
            True if any cubes are currently being transposed.
        """
        with self._lock:
            if data_source not in self._states:
                return False
            return any(
                info.status == TransposeState.IN_PROGRESS 
                for info in self._states[data_source].values()
            )
    
    def get_transposed_path(self, data_source: str, cube_file: str) -> Optional[str]:
        """
        Get the path to a transposed file if it exists and is completed.
        
        Args:
            data_source: Name of the data source.
            cube_file: Name/path of the cube file.
            
        Returns:
            Path to transposed file if completed successfully, None otherwise.
        """
        info = self.get_status(data_source, cube_file)
        if info.status == TransposeState.COMPLETED:
            return info.transposed_path
        return None
