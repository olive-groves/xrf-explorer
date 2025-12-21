import { appState } from "@/lib/appState";
import { computed, ref } from "vue";

export interface StitchPoint {
  id: number;
  gray: { x: number; y: number };
  base?: { x: number; y: number };
}

// Rotation per grayscale
export const grayscaleRotation = ref<Record<number, number>>({});

// max points per grayscale
export const maxPoints = 4;

// Points per grayscale, keyed by grayscale index
export const grayscalePoints = ref<Record<number, StitchPoint[]>>({});

// Selected point per grayscale
export const selectedPointId = ref<number | null>(null);
export const selectedGrayscaleIndex = ref<number | null>(null);

export function setSelectedGrayscaleIndex(i: number | null) {
  selectedGrayscaleIndex.value = i;
  selectedPointId.value = null; 
}

export function getPointsForGray(idx: any): StitchPoint[] {
  if (!grayscalePoints.value[idx]) grayscalePoints.value[idx] = [];
  return grayscalePoints.value[idx];
}


export function createGrayPoint(x: number, y: number) {
  if (selectedGrayscaleIndex.value === null) return;
  const idx = selectedGrayscaleIndex.value;
  const points = getPointsForGray(idx);
  if (points.length >= maxPoints) return;

  const id = points.length;
  points.push({ id, gray: { x, y } });
  selectedPointId.value = id;
}

export function updateGrayPoint(id: number | null, x: number, y: number) {
  if (selectedGrayscaleIndex.value === null) return;
  const points = getPointsForGray(selectedGrayscaleIndex.value);
  const p = points.find(p => p.id === id);
  if (p) p.gray = { x, y };
}

export function updateBasePoint(id: number | null, x: number, y: number) {
  if (selectedGrayscaleIndex.value === null) return;
  const points = getPointsForGray(selectedGrayscaleIndex.value);
  const p = points.find(p => p.id === id);
  if (p) p.base = { x, y };
}

export function selectPoint(id: number | null) {
  selectedPointId.value = id;
}

export function checkSelectPoint(id: number | null) {
  return selectedPointId.value === id;
}

export function deselect(){
  selectedPointId.value = null;
}

export function getRotation(idx: number): number {
  return grayscaleRotation.value[idx] ?? 0;
}

export function setRotation(idx: number, rot: number) {
  const snapped = Math.round(rot / 90) * 90;
  const clamped = Math.max(-180, Math.min(180, snapped));
  grayscaleRotation.value[idx] = clamped;

  window.dispatchEvent(new CustomEvent("stitch:grayscale-prop-changed", {
    detail: { index: idx, prop: "rotation", value: clamped }
  }));
}


export function getFlatMap<T>(
  mapper: (p: StitchPoint, grayIndex: number) => T | T[]
): T[] {
  const result: T[] = [];

  for (const [idxStr, points] of Object.entries(grayscalePoints.value)) {
    const idx = Number(idxStr);

    for (const p of points) {
      const mapped = mapper(p, idx);
      if (Array.isArray(mapped)) result.push(...mapped);
      else result.push(mapped);
    }
  }

  return result;
}


export function hasBase(p: StitchPoint): p is StitchPoint & { base: { x: number; y: number } } {
  return p.base !== undefined;
}


/**
 * Returns true if all grayscale images have all points mapped (gray + base).
 */
export const canPreview = computed(() => {
  const grays = appState.workspace?.grayscale ?? [];
  if (grays.length === 0) return false;

  return grays.every((_, idx) => {
    const points = grayscalePoints.value[idx] ?? [];
    return points.length === maxPoints && points.every(p => p.base?.x != null && p.base?.y != null);
  });
});

type CornerKey = "top_left" | "top_right" | "bottom_left" | "bottom_right";

function pointsToBackendDicts(points: StitchPoint[]): {
  local_points: Record<CornerKey, [number, number]>;
  target_points: Record<CornerKey, [number, number]>;
} {
  if (points.length !== maxPoints) {
    throw new Error(`Expected ${maxPoints} points, got ${points.length}`);
  }

  if (!points.every(hasBase)) {
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

export function buildFragmentsForAPI() {
  const ws = appState.workspace;
  if (!ws) return [];

  return ws.grayscale.map((gray, idx) => {
    const points = getPointsForGray(idx);
    const { local_points, target_points } = pointsToBackendDicts(points);

    let datacube_file: string;
    let rpl_file: string | undefined;

    if (gray.sourceCubeType === "elemental") {
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