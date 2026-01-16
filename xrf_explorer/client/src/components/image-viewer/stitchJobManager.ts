export type StitchType = "elemental" | "spectral";

export interface JobStatus<T = unknown> {
  job_id: string;
  status: "in_progress" | "completed" | "failed";
  result?: T;
  error?: string;
}

export interface PendingJob<T extends string = string> {
  type: T;
  jobId: string;
}

export interface PollOptions<T extends string = string> {
  intervalMs?: number;
  onJobComplete?: (job: PendingJob<T>) => void;
  onJobFailed?: (job: PendingJob<T>, error: string) => void;
}

/**
 * Fetches job status from a polling endpoint.
 */
export async function fetchJobStatus<T = unknown>(
  url: string
): Promise<JobStatus<T>> {
  const resp = await fetch(url);
  const data = await resp.json();

  if (!resp.ok) {
    throw new Error(data.error ?? "Failed to get job status");
  }

  return data;
}

/**
 * Polls multiple jobs until all complete or one fails.
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
          const message =
            error instanceof Error ? error.message : "Unknown error";
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
