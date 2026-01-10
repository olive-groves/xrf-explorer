<script lang="ts" setup>
import { computed, reactive, watch } from "vue";
import {
  selectedGrayscaleIndex,
  updateGrayPoint,
  updateBasePoint,
  maxPoints,
  createGrayPoint,
  clearAllPoints,
} from "./stitchPoints";
import StitchMappingBase from "./StitchMappingBase.vue";
import StitchMappingGreyscale from "./StitchMappingGreyscale.vue";
import { appState } from "@/lib/appState";
import { getTooltipByKey } from "@/lib/useToolTips";

// --- Selected grayscale and points ---
const selectedIndex = computed(() => selectedGrayscaleIndex.value);

const grayscalePoints = computed(() => {
  const ws = appState.workspace;
  if (ws) {
    return ws.mapping.grayscalePoints ?? [];
  }
  return [];
});

const points = computed(() => {
  if (selectedIndex.value === null || grayscalePoints.value === undefined) return [];
  return grayscalePoints.value[selectedIndex.value] ?? [];
});

// --- Editable buffers ---
const editGray = reactive<Record<number, { x: number; y: number }>>({});
const editBase = reactive<Record<number, { x: number; y: number }>>({});

// --- Ensure 4 editors and populate with existing points ---
watch(
  [points, grayscalePoints],
  () => {
    if (selectedIndex.value === null) return;

    for (let i = 0; i < maxPoints; i++) {
      const p = points.value?.find((pt) => pt.id === i);
      editGray[i] = { x: p?.gray.x ?? 0, y: p?.gray.y ?? 0 };
      editBase[i] = { x: p?.base?.x ?? 0, y: p?.base?.y ?? 0 };
    }
  },
  { immediate: true, deep: true },
);

/**
 * Function to update grayscale point.
 * @param id - Point identifier.
 */
function updateGray(id: number) {
  const p = editGray[id];
  if (!p) return;

  if (!points.value?.find((pt) => pt.id === id)) {
    createGrayPoint(p.x, p.y);
  } else {
    updateGrayPoint(id, p.x, p.y);
  }
}

/**
 * Function to update base point.
 * @param id - Point identifier.
 */
function updateBase(id: number) {
  const p = editBase[id];
  if (!p) return;
  updateBasePoint(id, p.x, p.y);
}

// --- Editors indices ---
const editors = Array.from({ length: maxPoints }, (_, i) => i);
</script>

<template>
  <div class="flex size-full flex-col">
    <!-- Image viewers grow to fill available space -->
    <div class="flex w-full grow border-b border-black">
      <!-- Left = greyscale -->
      <div class="w-1/2 border-r border-black">
        <StitchMappingGreyscale class="size-full" />
      </div>

      <!-- Right = base -->
      <div class="w-1/2">
        <StitchMappingBase class="size-full" />
      </div>
    </div>

    <!-- Points editor -->
    <div class="relative z-10 w-full shrink-0 p-1 text-sm">
      <div v-if="selectedIndex !== null" class="flex items-start gap-1">
        <div v-for="id in editors" :key="id" class="flex w-48 shrink-0 flex-col gap-1 rounded border p-1 shadow">
          <div class="text-center text-xs font-semibold">Point {{ id + 1 }}</div>

          <!-- Grayscale coords -->
          <div class="flex gap-1">
            <label class="flex flex-col items-center text-xs">
              Greyscale X
              <input
                type="number"
                class="pointer-events-auto w-20 border bg-white p-1 text-black dark:border-gray-600 dark:bg-black
                  dark:text-white"
                v-model.number="editGray[id].x"
                @change="updateGray(id)"
                :placeholder="points[id]?.gray.x != null ? String(points[id].gray.x) : '--'"
              />
            </label>
            <label class="flex flex-col items-center text-xs">
              Greyscale Y
              <input
                type="number"
                class="pointer-events-auto w-20 border bg-white p-1 text-black dark:border-gray-600 dark:bg-black
                  dark:text-white"
                v-model.number="editGray[id].y"
                @change="updateGray(id)"
                :placeholder="points[id]?.gray.y != null ? String(points[id].gray.y) : '--'"
              />
            </label>
          </div>

          <!-- Base coords -->
          <div class="flex gap-1">
            <label class="flex flex-col items-center text-xs">
              Base X
              <input
                type="number"
                class="pointer-events-auto w-20 border bg-white p-1 text-black dark:border-gray-600 dark:bg-black
                  dark:text-white"
                v-model.number="editBase[id].x"
                @change="updateBase(id)"
                :placeholder="points[id]?.base?.x != null ? String(points[id]?.base?.x) : '--'"
              />
            </label>
            <label class="flex flex-col items-center text-xs">
              Base Y
              <input
                type="number"
                class="pointer-events-auto w-20 border bg-white p-1 text-black dark:border-gray-600 dark:bg-black
                  dark:text-white"
                v-model.number="editBase[id].y"
                @change="updateBase(id)"
                :placeholder="points[id]?.base?.y != null ? String(points[id]?.base?.y) : '--'"
              />
            </label>
          </div>
        </div>
        <Button @click="clearAllPoints" :title="getTooltipByKey('stitch.clear_points')">Clear points</Button>
      </div>
      <div v-else class="text-xs italic text-gray-600">No grayscale selected.</div>
    </div>
  </div>
</template>
