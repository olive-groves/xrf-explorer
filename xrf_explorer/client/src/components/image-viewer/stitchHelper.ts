import { appState } from "@/lib/appState";
import { canPreview, getPointsForGray, getRotation, hasBase, maxPoints, StitchPoint } from "./stitchPoints";
import { toast } from "vue-sonner";
import { ref } from "vue";
import { saveWorkspaceDebounced, saveWorkspaceToBackend } from "./workspace";
import { windowState } from "../ui/window/state";
import { PendingJob, pollJobs, StitchType } from "./stitchJobManager.ts";

type CornerKey = "top_left" | "top_right" | "bottom_left" | "bottom_right";

function pointsToBackendDicts(points: StitchPoint[]): {
  local_points: Record<CornerKey, [number, number]>;
  target_points: Record<CornerKey, [number, number]>;
} {
  if (points.length !== maxPoints) {
    toast.error(`Stitch error`, {
          description: `Expected ${maxPoints} points, got ${points.length}`,
    });
    throw new Error(`Expected ${maxPoints} points, got ${points.length}`);

  }

  if (!points.every(hasBase)) {
    toast.error(`Stitch error`, {
          description: "All stitch points must have base coordinates before preview.",
    });
    throw new Error("All stitch points must have base coordinates before preview.");
  }

  const pts = points as (StitchPoint & { base: { x: number; y: number } })[];

  const sortedByBase = [...pts].sort(
    (a, b) => (a.base.y - b.base.y) || (a.base.x - b.base.x)
  );

  const topTwo = sortedByBase.slice(0, 2).sort((a, b) => a.base.x - b.base.x);
  const bottomTwo = sortedByBase.slice(2, 4).sort((a, b) => a.base.x - b.base.x);

  const ordered: Record<CornerKey, typeof pts[number]> = {
    top_left: topTwo[0],
    top_right: topTwo[1],
    bottom_left: bottomTwo[0],
    bottom_right: bottomTwo[1],
  };

  return {
    local_points: {
      top_left: [ordered.top_left.gray.x, ordered.top_left.gray.y],
      top_right: [ordered.top_right.gray.x, ordered.top_right.gray.y],
      bottom_left: [ordered.bottom_left.gray.x, ordered.bottom_left.gray.y],
      bottom_right: [ordered.bottom_right.gray.x, ordered.bottom_right.gray.y],
    },
    target_points: {
      top_left: [ordered.top_left.base.x, ordered.top_left.base.y],
      top_right: [ordered.top_right.base.x, ordered.top_right.base.y],
      bottom_left: [ordered.bottom_left.base.x, ordered.bottom_left.base.y],
      bottom_right: [ordered.bottom_right.base.x, ordered.bottom_right.base.y],
    },
  };
}

export function buildFragmentsForAPI(type: StitchType) {
  const ws = appState.workspace;
  if (!ws) return [];

  if (type === "elemental") {
    return ws.partialElementalCubes.map((cube, idx) => {
      const points = getPointsForGray(idx);
      const { local_points, target_points } = pointsToBackendDicts(points);

      return {
        datacube_file: cube.dataLocation,
        rotation: (getRotation(idx) + 360) % 360,
        local_points,
        target_points,
      };
    });
  } else {
    return ws.partialSpectralCubes.map((cube, idx) => {
      const points = getPointsForGray(idx);
      const { local_points, target_points } = pointsToBackendDicts(points);

      return {
        datacube_file: cube.rawLocation,
        ...(cube.rplLocation ? { rpl_file: cube.rplLocation } : {}),
        rotation: (getRotation(idx) + 360) % 360,
        local_points,
        target_points,
      };
    });
  }
}

/**
 * Starts a stitch job and waits for completion.
 * Useful for quick preview stitches.
 * Used for preview stitching
 */
export async function stitchAndWait(
  preview: boolean,
  type: StitchType,
  scaling_factor: number,
  intensity: number[],
  pollIntervalMs = 500,
): Promise<void> {
  const ws = appState.workspace;
  if (!ws) throw new Error("No workspace");

  const jobId = await startStitchJob(preview, type, scaling_factor, intensity);

  await pollJobs(
    [{ type, jobId }],
    (job) => `/api/${ws.name}/stitch_datacubes/stitch_status/${job.jobId}`,
    {
      intervalMs: pollIntervalMs,
      onJobFailed: (job, error) => {
        toast.error(`Stitch failed (${job.type})`, { description: error });
      },
    }
  );
}

/**
 * Starts a stitch job and returns the job_id.
 */
async function startStitchJob(
  preview: boolean,
  type: StitchType,
  scaling_factor: number,
  intensity: number[]
): Promise<string> {
  const ws = appState.workspace;
  if (!ws) throw new Error("No workspace");

  const fragments = buildFragmentsForAPI(type);
  if (fragments.length === 0) throw new Error("No fragments to stitch");

  const payload = {
    type,
    preview: preview,
    contextual_image: ws.baseImage.imageLocation,
    down_scaling: scaling_factor,
    intensity_scales: intensity,
    fragments,
  };

  const resp = await fetch(
    `/api/${ws.name}/stitch_datacubes/stitch`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }
  );

  const data = await resp.json();
  if (!resp.ok) {
    const message = data.error ?? JSON.stringify(data);
    toast.error(`Stitch error`, {
          description: message,
    });
    throw new Error(message);
  }

  return data.job_id;
}

export async function fetchOptimalStitchInfo(): Promise<{
  losses: number[] | null;
  estimatedSize: number;
  optimalScaling: number;
} | null> {
  if (!appState.workspace) return null;
  if (!canPreview.value) return null;

  const ws = appState.workspace;
  const type = ws.grayscale[0].sourceCubeType;
  const fragments = buildFragmentsForAPI(type);
  if (fragments.length === 0) return null;

  const payload = {
    type,
    contextual_image: ws.baseImage.imageLocation,
    down_scaling: 1,
    fragments,
  };

  const resp = await fetch(
    `/api/${ws.name}/stitch_datacubes/get_stitch_info`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }
  );

  const result = await resp.json();

  if (!resp.ok) {
    const message = result.error ?? JSON.stringify(result);
    toast.error(`Stitch error`, { description: message });
    throw new Error(message);
  }

  return {
    losses: result.losses ?? null,
    estimatedSize:
      Math.round((result.full_size / (1024 * 1024 * 1024)) * 10000) / 10000,
    optimalScaling: result.optimalScaling,
  };
}

//Wether we are busy with stitching
export const stitchingInProgress = ref(false);

/**
 * Start stitching the selected cubes.
 * @param includeSpectral - Whether to stitch spectral cubes
 * @param includeElemental - Whether to stitch elemental cubes
 */
export async function confirmStitching(includeSpectral: boolean, includeElemental: boolean, scaling_factor: number) {
  const ws = appState.workspace;
  if (!ws) return;
  windowState["stitching"].opened = false;
  windowState["stitching"].disabled = true;

  stitchingInProgress.value = true;

  const intensities = ws.grayscale.map(
    (_, idx) => ws.mapping.grayscaleContrast?.[idx] ?? 1.0
  );
  await saveWorkspaceToBackend();

  const pendingJobs: PendingJob<StitchType>[] = [];

  try {
    if (includeElemental) {
      ws.elementalCubes = [];
      const jobId = await startStitchJob(
        false,
        "elemental",
        scaling_factor,
        intensities
      );
      pendingJobs.push({ type: "elemental", jobId });
    }

    if (includeSpectral) {
      ws.spectralCubes = [];
      const jobId = await startStitchJob(
        false,
        "spectral",
        scaling_factor,
        intensities
      );
      pendingJobs.push({ type: "spectral", jobId });
    }

    await pollJobs(
      pendingJobs,
      (job) => `/api/${ws.name}/stitch_datacubes/stitch_status/${job.jobId}`,
      {
        onJobFailed: (job, error) => {
          toast.error(`Stitch failed (${job.type})`, { description: error });
        },
      }
    );

    // All jobs completed - fetch updated workspace
    const resp = await fetch(`/api/${ws.name}/workspace`, { cache: "no-store" });
    if (resp.ok) {
      const updated = await resp.json();
      updated.stitchingMode = "full";
      updated.mapping.mode = "edit";
      appState.workspace = updated;
      saveWorkspaceDebounced();
    }
  } catch {
    // Error already handled via onJobFailed
  } finally {
    stitchingInProgress.value = false;
    windowState["stitching"].disabled = false;
  }
}