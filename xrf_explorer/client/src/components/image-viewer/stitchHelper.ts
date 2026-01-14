import { appState } from "@/lib/appState";
import { canPreview, getPointsForGray, getRotation, hasBase, maxPoints, StitchPoint } from "./stitchPoints";
import { toast } from "vue-sonner";
import { ref } from "vue";
import { saveWorkspaceDebounced } from "./workspace";
import { windowState } from "../ui/window/state";

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

export function buildFragmentsForAPI(type: "elemental" | "spectral") {
  const ws = appState.workspace;
  if (!ws) return [];

  if (type === "elemental") {
    return ws.partialElementalCubes.map((cube, idx) => {
      const points = getPointsForGray(idx);
      const { local_points, target_points } = pointsToBackendDicts(points);

      return {
        datacube_file: cube.dataLocation, // Now compiler knows this exists
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
        datacube_file: cube.rawLocation, // Now compiler knows this exists
        ...(cube.rplLocation ? { rpl_file: cube.rplLocation } : {}),
        rotation: (getRotation(idx) + 360) % 360,
        local_points,
        target_points,
      };
    });
  }
}

// Generate geryscale preview
export async function stitch(preview: boolean, type: "elemental" | "spectral", scaling_factor: number, intensity: number[]) {
  if (!appState.workspace) return;
  const ws = appState.workspace;

  const fragments = buildFragmentsForAPI(type);
  if (fragments.length === 0) return;

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
export function confirmStitching(includeSpectral: boolean, includeElemental: boolean, scaling_factor: number) {
  const ws = appState.workspace;
  if (!ws) return;
  windowState["stitching"].opened = false;
  windowState["stitching"].disabled = true;

  stitchingInProgress.value = true;

  const intensities = ws.grayscale.map(
    (_, idx) => ws.mapping.grayscaleContrast?.[idx] ?? 1.0
  );

  if (includeElemental) {
    stitch(false, "elemental", scaling_factor, intensities);
  }
  if (includeSpectral) {
    stitch(false, "spectral", scaling_factor, intensities);
  }

  const interval = setInterval(async () => {
    const resp = await fetch(`/api/${ws.name}/workspace`);
    if (!resp.ok) return;

    const updated = await resp.json();

    const spectralDone =
      !includeSpectral || (updated.spectralCubes?.length ?? 0) > 0;
    const elementalDone =
      !includeElemental || (updated.elementalCubes?.length ?? 0) > 0;

    if (spectralDone && elementalDone) {
      clearInterval(interval);

      appState.workspace = updated;

      stitchingInProgress.value = false;
      saveWorkspaceDebounced();
    }
  }, 2000);
}



