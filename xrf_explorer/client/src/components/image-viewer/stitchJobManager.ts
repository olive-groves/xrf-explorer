/**
 * Types and utilities for managing stitch jobs.
 */
export type StitchType = "elemental" | "spectral";

/**
 * Interfaces to keep track of the stitch jobs and their states.
 */
export interface JobStatus<T = unknown> {
  /**
   * Job ID.
   */
  job_id: string;
  /**
   * Status of the job.
   */
  status: "in_progress" | "completed" | "failed";
  /**
   * Result of the job if completed.
   */
  result?: T;
  /**
   * Error message if failed.
   */
  error?: string;
}

/**
 * Pending job information.
 */
export interface PendingJob<T extends string = string> {
  /**
   * Type of the job.
   */
  type: T;
  /**
   * Job ID.
   */
  jobId: string;
}

/**
 * Options for polling jobs.
 */
export interface PollOptions<T extends string = string> {
  /**
   * Polling interval in milliseconds.
   */
  intervalMs?: number;
  /**
   * Callback when a job completes.
   */
  onJobComplete?: (job: PendingJob<T>) => void;
  /**
   * Callback when a job fails.
   */
  onJobFailed?: (job: PendingJob<T>, error: string) => void;
}

/**
 * Fetches job status from a polling endpoint.
 * @param url - The job status URL.
 * @returns The job status.
 */
export async function fetchJobStatus<T = unknown>(url: string): Promise<JobStatus<T>> {
  const resp = await fetch(url);
  const data = await resp.json();

  if (!resp.ok) {
    throw new Error(data.error ?? "Failed to get job status");
  }

  return data;
}

/**
 * Polls multiple jobs until all complete or one fails.
 * @param jobs - The jobs to poll.
 * @param getStatusUrl - Function to get the status URL for a job.
 * @param options - Polling options.
 * @returns Promise that resolves when all jobs complete, rejects if any fail.
 */
export function pollJobs<T extends string>(
  jobs: PendingJob<T>[],
  getStatusUrl: (job: PendingJob<T>) => string,
  options: PollOptions = {},
): Promise<void> {
  const { intervalMs = 2000, onJobComplete, onJobFailed } = options;
  const pending = [...jobs];

  return new Promise((resolve, reject) => {
    const interval = setInterval(async () => {
      for (let i = pending.length - 1; i >= 0; i--) {
        const job = pending[i];

        try {
          const status = await fetchJobStatus(getStatusUrl(job));

          if (status.status === "completed") {
            pending.splice(i, 1);
            onJobComplete?.(job);
          } else if (status.status === "failed") {
            clearInterval(interval);
            onJobFailed?.(job, status.error ?? "Unknown error");
            reject(new Error(status.error ?? `Job ${job.type} failed`));
            return;
          }
        } catch (error) {
          clearInterval(interval);
          const message = error instanceof Error ? error.message : "Unknown error";
          onJobFailed?.(job, message);
          reject(error);
          return;
        }
      }

      if (pending.length === 0) {
        clearInterval(interval);
        resolve();
      }
    }, intervalMs);
  });
}
