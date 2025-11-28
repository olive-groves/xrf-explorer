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

function getPointsForGray(idx: number): StitchPoint[] {
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

export function updateGrayPoint(id: number, x: number, y: number) {
  if (selectedGrayscaleIndex.value === null) return;
  const points = getPointsForGray(selectedGrayscaleIndex.value);
  const p = points.find(p => p.id === id);
  if (p) p.gray = { x, y };
}

export function updateBasePoint(id: number, x: number, y: number) {
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