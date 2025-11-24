import { ref } from "vue";

export interface StitchPoint {
  id: number;
  gray: { x: number; y: number };
  base?: { x: number; y: number };
}

export const maxPoints = 4;

// All point-mappings
export const stitchPoints = ref<StitchPoint[]>([]);

// Which point is currently selected (both views must highlight it)
export const selectedPointId = ref<number | null>(null);

// Helpers
export function createGrayPoint(x: number, y: number) {
  if (stitchPoints.value.length >= maxPoints) return;

  const id = stitchPoints.value.length;

  stitchPoints.value.push({
    id,
    gray: { x, y }
  });

  selectedPointId.value = id;
}

export function updateGrayPoint(id: number, x: number, y: number) {
  const p = stitchPoints.value.find(p => p.id === id);
  if (p) p.gray = { x, y };
}

export function updateBasePoint(id: number, x: number, y: number) {
  const p = stitchPoints.value.find(p => p.id === id);
  if (p) p.base = { x, y };
}

export function selectPoint(id: number | null) {
  selectedPointId.value = id;
}

export function checkSelectPoint(id: number | null) {
  return selectedPointId.value == id;
}

export function deselect(){
  selectedPointId.value = null;
}