<script setup lang="ts">
import { LabeledSlider } from "@/components/ui/slider";
import { getRotation, setRotation } from "@/components/image-viewer/stitchPoints";
import { getWorkspaceGreyscaleUrl } from "@/components/image-viewer/workspace";
import { appState } from "@/lib/appState";
import { computed, onMounted, ref } from "vue";

const workspace = computed(() => appState.workspace);

// The index of the currently selected greyscale
const selectedGreyscale = ref<number | null>(0);

/**
 * Function the change the selected greyscale.
 * @param idx - The index of the newly selected greyscale.
 */
function selectGreyscale(idx: number) {
  selectedGreyscale.value = idx;

  // Notify the mapping viewer so it can change shown greyscale
  window.dispatchEvent(new CustomEvent("stitch:selected-grayscale", { detail: idx }));
}

onMounted(() => {
  if (selectedGreyscale.value !== null) {
    window.dispatchEvent(new CustomEvent("stitch:selected-grayscale", { detail: selectedGreyscale.value }));
  }
});
</script>

<template>
  <Window title="Stitching" location="right">
    <div class="space-y-4 p-4">
      <h3 class="text-lg font-semibold">Select a Fragment</h3>

      <!-- An image per greyscale for selection -->
      <div class="grid grid-cols-2 gap-4">
        <div
          v-for="(greyscale, idx) in workspace?.grayscale"
          :key="idx"
          class="cursor-pointer overflow-hidden rounded-md border transition"
          :class="{
            'ring-4 ring-blue-500': selectedGreyscale === idx,
            'hover:ring-2 hover:ring-blue-300': selectedGreyscale !== idx,
          }"
          @click="selectGreyscale(idx)"
        >
          <div class="flex h-32 w-full items-center justify-center bg-gray-100 pt-4 dark:bg-black">
            <img
              class="max-h-full max-w-full object-contain"
              :src="getWorkspaceGreyscaleUrl(greyscale.imageLocation)"
              :alt="`Greyscale ${greyscale.sourceCubeName}`"
            />
          </div>
          <div class="bg-gray-50 p-1 text-center text-sm dark:bg-black dark:text-gray-200">
            {{ greyscale.sourceCubeName }}
          </div>
          <!-- A slider per greyscale for selecting rotation -->
          <div class="mt-2 rounded-md border p-2">
            <LabeledSlider
              label="Rotation"
              :model-value="[getRotation(idx)]"
              :min="-180"
              :max="180"
              :step="90"
              @update:model-value="(val: number[]) => setRotation(idx, val[0])"
            />
          </div>
        </div>
      </div>
    </div>
  </Window>
</template>
