import { appState } from "@/lib/appState";
import { canPreview, getPointsForGray, getRotation, hasBase, maxPoints, StitchPoint } from "./stitchPoints";
import { toast } from "vue-sonner";

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

  return ws.grayscale.map((gray, idx) => {
    const points = getPointsForGray(idx);
    const { local_points, target_points } = pointsToBackendDicts(points);

    let datacube_file: string;
    let rpl_file: string | undefined;

    if (type === "elemental") {
      datacube_file =
        ws.partialElementalCubes.find(c => c.name === gray.sourceCubeName)!.dataLocation;
    } else {
      const cube =
        ws.partialSpectralCubes.find(c => c.name === gray.sourceCubeName)!;
      datacube_file = cube.rawLocation;
      rpl_file = cube.rplLocation;
    }

    return {
      datacube_file,
      ...(rpl_file ? { rpl_file } : {}),
      rotation: getRotation(idx),
      local_points,
      target_points,
    };
  });
}

// Generate geryscale preview
export async function stitch(preview: boolean, type: "elemental" | "spectral") {
  if (!appState.workspace) return;
  const ws = appState.workspace;

  const fragments = buildFragmentsForAPI(type);
  if (fragments.length === 0) return;

  const payload = {
    type,
    preview: preview,
    contextual_image: ws.baseImage.imageLocation,
    down_scaling: 1,
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
  const type = ws.grayscale[0].sourceCubeType
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

  const data = await resp.json();
  if (!resp.ok) {
    const message = data.error ?? JSON.stringify(data);
    toast.error(`Stitch error`, {
          description: message,
    });
    throw new Error(message);
  }

  const result = await resp.json();

  return {
    losses: result.losses ?? null,
    estimatedSize:
      Math.round(
        (result.full_size / (1024 * 1024 * 1024)) * 10000
      ) / 10000,
    optimalScaling: result.optimalScaling
  };
}

