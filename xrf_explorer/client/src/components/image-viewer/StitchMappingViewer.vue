<script lang="ts" setup>
import { computed, reactive, watch } from "vue";
import StitchMappingBase from "./StitchMappingBase.vue";
import StitchMappingGreyscale from "./StitchMappingGreyscale.vue";

import {
  grayscalePoints,
  selectedGrayscaleIndex,
  updateGrayPoint,
  updateBasePoint,
  maxPoints,
  createGrayPoint
} from "./stitchPoints";

// --- Selected grayscale and points ---
const selectedIndex = computed(() => selectedGrayscaleIndex.value);

const points = computed(() => {
  if (selectedIndex.value === null) return [];
  return grayscalePoints.value[selectedIndex.value] ?? [];
});

// --- Editable buffers ---
const editGray = reactive<Record<number, { x: number; y: number }>>({});
const editBase = reactive<Record<number, { x: number; y: number }>>({});

// --- Ensure 4 editors and populate with existing points ---
watch([points, grayscalePoints], () => {
  if (selectedIndex.value === null) return;

  for (let i = 0; i < maxPoints; i++) {
    const p = points.value.find(pt => pt.id === i);
    editGray[i] = { x: p?.gray.x ?? 0, y: p?.gray.y ?? 0 };
    editBase[i] = { x: p?.base?.x ?? 0, y: p?.base?.y ?? 0 };
  }
}, { immediate: true, deep: true });

// --- Update functions ---
function updateGray(id: number) {
  const p = editGray[id];
  if (!p) return;

  if (!points.value.find(pt => pt.id === id)) {
    createGrayPoint(p.x, p.y);
  } else {
    updateGrayPoint(id, p.x, p.y);
  }
}

function updateBase(id: number) {
  const p = editBase[id];
  if (!p) return;
  updateBasePoint(id, p.x, p.y);
}

// --- Editors indices ---
const editors = Array.from({ length: maxPoints }, (_, i) => i);
</script>

<template>
  <div class="flex flex-col w-full h-full">
    <!-- Image viewers grow to fill available space -->
    <div class="flex w-full flex-grow border-b border-black">
      <div class="w-1/2 border-r border-black">
        <StitchMappingGreyscale class="w-full h-full" />
      </div>
      <div class="w-1/2">
        <StitchMappingBase class="w-full h-full" />
      </div>
    </div>

    <!-- Compact Points editor -->
    <div class="w-full p-1 bg-gray-100 text-sm flex-shrink-0 relative z-10">
      <div v-if="selectedIndex !== null" class="flex gap-1 items-start">
        <div
          v-for="id in editors"
          :key="id"
          class="flex-shrink-0 p-1 border rounded bg-white shadow flex flex-col gap-1 w-48"
        >
          <div class="font-semibold text-center text-xs">Point {{ id + 1 }}</div>

          <!-- Grayscale coords -->
          <div class="flex gap-1">
            <label class="flex flex-col items-center text-xs">
              Greyscale X
              <input
                type="number"
                class="border p-1 w-20 pointer-events-auto"
                v-model.number="editGray[id].x"
                @change="updateGray(id)"
                :placeholder="points[id]?.gray.x != null ? String(points[id].gray.x) : '--'"
              />
            </label>
            <label class="flex flex-col items-center text-xs">
              Greyscale Y
              <input
                type="number"
                class="border p-1 w-20 pointer-events-auto"
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
                class="border p-1 w-20 pointer-events-auto"
                v-model.number="editBase[id].x"
                @change="updateBase(id)"
                :placeholder="points[id]?.base?.x != null ? String(points[id].base.x) : '--'"
              />
            </label>
            <label class="flex flex-col items-center text-xs">
              Base Y
              <input
                type="number"
                class="border p-1 w-20 pointer-events-auto"
                v-model.number="editBase[id].y"
                @change="updateBase(id)"
                :placeholder="points[id]?.base?.y != null ? String(points[id].base.y) : '--'"
              />
            </label>
          </div>
        </div>
      </div>
      <div v-else class="italic text-gray-600 text-xs">No grayscale selected.</div>
    </div>
  </div>
</template>