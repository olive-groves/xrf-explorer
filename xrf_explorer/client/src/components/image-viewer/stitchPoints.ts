import { appState } from "@/lib/appState";
import { computed, ref } from "vue";
import { saveWorkspaceDebounced } from "./workspace";

// Data structure to store the 4 mapped points per greyscale
export interface StitchPoint {
  // Greyscale index
  id: number;
  // Points in the greyscale
  gray: { x: number; y: number };
  // Corresponding base image points
  base?: { x: number; y: number };
}

// max points per grayscale
export const maxPoints = 4;

// Selected point per grayscale
export const selectedPointId = ref<number | null>(null);
export const selectedGrayscaleIndex = ref<number | null>(null);

/**
 * Fucntion to change the selected greyscale
 * @param i the newly selected greyscale
 */
export function setSelectedGrayscaleIndex(i: number | null) {
  selectedGrayscaleIndex.value = i;
  selectedPointId.value = null; 
}

/**
 * Function to clear all mapping points
 */
export function clearAllPoints() {
  const ws = appState.workspace;
  if (!ws) return;
  for (const k of Object.keys(ws.mapping.grayscalePoints)) {
    delete ws.mapping.grayscalePoints[Number(k)];
  }
  selectedPointId.value = null;
  saveWorkspaceDebounced();
}

/**
 * Gets the stiched points for a given greysclale
 * @param idx - The greyscale index for which you want to points
 * @returns - The mapped points for greyscale idx
 */
export function getPointsForGray(idx: number): StitchPoint[] {
  const ws = appState.workspace;
  if (!ws) return [];
  if (!ws.mapping.grayscalePoints[idx]) {
    ws.mapping.grayscalePoints[idx] = [];
  }
  return ws.mapping.grayscalePoints[idx];
}

/**
 * Creates a grayscale point
 * @param x - x coordinate of created point
 * @param y - y coordinate of created point
 */
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

/**
 * Updates the coordinates of a greyscale point
 * @param id - The id of the point that is changed
 * @param x - The new x coordinate
 * @param y - The new y coordinate
 */
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

/**
 * Updates the coordinates of a base point
 * @param id - The id of the point that is changed
 * @param x - The new x coordinate
 * @param y - The new y coordinate
 */
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

/**
 * Function for selecting a point
 * @param id - The id of the point that is selected
 */
export function selectPoint(id: number | null) {
  selectedPointId.value = id;
}

/**
 * Check wether the selected point has a certain id
 * @param id - The id for which you want to check if it is the selected point
 * @returns true if the selected point has id "id", false otherwise
 */
export function checkSelectPoint(id: number | null) {
  return selectedPointId.value === id;
}

/**
 * Deselect a point
 */
export function deselect(){
  selectedPointId.value = null;
}

/**
 * Get the rotation value of a greyscale
 * @param idx - The greyscale index
 * @returns The rotation of greyscale idx
 */
export function getRotation(idx: number): number {
  return appState.workspace?.mapping.grayscaleRotation[idx] ?? 0;
}

/**
 * Set the rotation of a greyscale
 * @param idx - The index of the greyscale
 * @param rot - The new roation value 
 */
export function setRotation(idx: number, rot: number) {
  // Snap it to intervals of 90 degrees
  const snapped = Math.round(rot / 90) * 90;
  const clamped = Math.max(-180, Math.min(180, snapped));
  const ws = appState.workspace;
  if (ws) {
    ws.mapping.grayscaleRotation[idx] = clamped;
  }
  // Inform stitchMappingGreyscale that the rotation has changed
  window.dispatchEvent(new CustomEvent("stitch:grayscale-prop-changed", {
    detail: { index: idx, prop: "rotation", value: clamped }
  }));
  saveWorkspaceDebounced();
}

/**
 * Iterates over all grayscale-mapped stitch points in the workspace and applies
 * a mapping function to each point. The results are flattened into a single array.
 *
 * @param mapper Function that maps a StitchPoint and its grayscale index to a value or an array of values.
 * @returns A flat array containing all mapped results.
 */
export function getFlatMap<T>(
  mapper: (p: StitchPoint, grayIndex: number) => T | T[]
): T[] {
  const ws = appState.workspace;
  if (!ws) return [];

  const result: T[] = [];

  for (const [idxStr, points] of Object.entries(ws.mapping.grayscalePoints)) {
    const idx = Number(idxStr);

    for (const p of points) {
      const mapped = mapper(p, idx);
      result.push(...(Array.isArray(mapped) ? mapped : [mapped]));
    }
  }
  return result;
}

/**
 * Check if a point has a base point
 * @param p - A stitchPoint
 * @returns - Wether the stitchPoint has a defined base point
 */
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

