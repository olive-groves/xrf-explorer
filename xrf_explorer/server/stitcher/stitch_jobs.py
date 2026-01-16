"""Background job management for stitching operations."""

import threading
import traceback
import uuid
from typing import Dict, Any, Optional

from logging import Logger, getLogger

from xrf_explorer.server.stitcher import stitch, StitchData

LOG: Logger = getLogger(__name__)

# Thread-safe storage for stitch job statuses
_stitch_jobs: Dict[str, Dict[str, Any]] = {}
_stitch_jobs_lock = threading.Lock()


def _run_stitch_job(job_id: str, stitch_configuration: StitchData):
    """Background worker that runs the stitch operation and updates job status."""
    try:
        result = stitch(stitch_configuration)
        with _stitch_jobs_lock:
            _stitch_jobs[job_id].update({
                "status": "completed",
                "result": result,
                "error": None
            })
    except FileNotFoundError as e:
        LOG.error(traceback.format_exc())
        with _stitch_jobs_lock:
            _stitch_jobs[job_id].update({
                "status": "failed",
                "error": f"File not found: {str(e)}",
                "error_type": "not_found"
            })
    except ValueError as e:
        LOG.error(traceback.format_exc())
        with _stitch_jobs_lock:
            _stitch_jobs[job_id].update({
                "status": "failed",
                "error": f"Validation error: {str(e)}",
                "error_type": "validation"
            })
    except Exception as e:
        LOG.error(traceback.format_exc())
        with _stitch_jobs_lock:
            _stitch_jobs[job_id].update({
                "status": "failed",
                "error": f"Stitching failed: {str(e)}",
                "error_type": "internal"
            })

def start_stitch_job(stitch_configuration: StitchData, data_source: str) -> str:
    """
    Starts a stitch job in the background.

    Args:
        stitch_configuration: Validated stitch configuration.
        data_source: Identifier for the data source.

    Returns:
        The job_id for polling status.
    """
    job_id = str(uuid.uuid4())

    with _stitch_jobs_lock:
        _stitch_jobs[job_id] = {
            "status": "in_progress",
            "data_source": data_source,
            "result": None,
            "error": None
        }

    thread = threading.Thread(
        target=_run_stitch_job,
        args=(job_id, stitch_configuration),
        daemon=True
    )
    thread.start()

    return job_id

def get_stitch_job_status(job_id: str, data_source: str) -> Optional[Dict[str, Any]]:
    """
    Gets the status of a stitch job.

    Args:
        job_id: The job ID to look up.
        data_source: The data source to verify ownership.

    Returns:
        Job status dict, or None if not found or wrong data_source.
    """
    with _stitch_jobs_lock:
        job = _stitch_jobs.get(job_id)

    if job is None or job["data_source"] != data_source:
        return None

    return {
        "job_id": job_id,
        "status": job["status"],
        "result": job["result"] if job["status"] == "completed" else None,
        "error": job["error"] if job["status"] == "failed" else None
    }