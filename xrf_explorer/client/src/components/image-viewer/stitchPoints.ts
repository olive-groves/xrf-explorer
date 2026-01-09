import { appState } from "@/lib/appState";
import { computed, ref } from "vue";
import { saveWorkspaceDebounced } from "./workspace";

export interface StitchPoint {
  id: number;
  gray: { x: number; y: number };
  base?: { x: number; y: number };
}

// max points per grayscale
export const maxPoints = 4;

// Selected point per grayscale
export const selectedPointId = ref<number | null>(null);
export const selectedGrayscaleIndex = ref<number | null>(null);

export function setSelectedGrayscaleIndex(i: number | null) {
  selectedGrayscaleIndex.value = i;
  selectedPointId.value = null; 
}

export function clearAllPoints() {
  const ws = appState.workspace;
  if (!ws) return;
  for (const k of Object.keys(ws.mapping.grayscalePoints)) {
    delete ws.mapping.grayscalePoints[Number(k)];
  }
  selectedPointId.value = null;
}

export function getPointsForGray(idx: number): StitchPoint[] {
  const ws = appState.workspace;
  if (!ws) return [];
  if (!ws.mapping.grayscalePoints[idx]) {
    ws.mapping.grayscalePoints[idx] = [];
  }
  return ws.mapping.grayscalePoints[idx];
}

export function createGrayPoint(x: number, y: number) {
  const ws = appState.workspace;
  const idx = selectedGrayscaleIndex.value;

  if (!ws || idx == null) return;
  const points = getPointsForGray(idx);
  if (points.length >= maxPoints) return;
  const id = points.length;
  points.push({
    id,
    gray: { x, y },
  });
  selectedPointId.value = id;
  saveWorkspaceDebounced();
}

export function updateGrayPoint(id: number | null, x: number, y: number) {
  const ws = appState.workspace;
  const idx = selectedGrayscaleIndex.value;

  if (!ws || idx == null || id == null) return;
  const points = getPointsForGray(idx);
  const p = points.find(p => p.id === id);
  if (!p) return;
  p.gray.x = x;
  p.gray.y = y;
  saveWorkspaceDebounced();
}

export function updateBasePoint(id: number | null, x: number, y: number) {
  const ws = appState.workspace;
  const idx = selectedGrayscaleIndex.value;

  if (!ws || idx == null || id == null) return;
  const points = getPointsForGray(idx);
  const p = points.find(p => p.id === id);
  if (!p) return;
  p.base = { x, y };
  saveWorkspaceDebounced();
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
  return appState.workspace?.mapping.grayscaleRotation[idx] ?? 0;
}

export function setRotation(idx: number, rot: number) {
  const snapped = Math.round(rot / 90) * 90;
  const clamped = Math.max(-180, Math.min(180, snapped));
  const ws = appState.workspace;
  if (ws) {
    ws.mapping.grayscaleRotation[idx] = clamped;
  }
  window.dispatchEvent(new CustomEvent("stitch:grayscale-prop-changed", {
    detail: { index: idx, prop: "rotation", value: clamped }
  }));
  saveWorkspaceDebounced();
}


export function getFlatMap<T>(
  mapper: (p: StitchPoint, grayIndex: number) => T | T[]
): T[] {
  const result: T[] = [];
  const ws = appState.workspace;
  if (ws) {
    for (const [idxStr, points] of Object.entries(ws.mapping.grayscalePoints)) {
      const idx = Number(idxStr);

      for (const p of points) {
        const mapped = mapper(p, idx);
        if (Array.isArray(mapped)) result.push(...mapped);
        else result.push(mapped);
      }
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
  const grayscalePoints = appState.workspace?.mapping.grayscalePoints
  if (!grayscalePoints) {return false}
  return grays.every((_, idx) => {
    const points = grayscalePoints[idx] ?? [];
    return points.length === maxPoints && points.every(p => p.base?.x != null && p.base?.y != null);
  });
});

