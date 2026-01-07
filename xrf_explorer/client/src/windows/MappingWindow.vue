<script setup lang="ts">
import { LabeledSlider } from "@/components/ui/slider";
import { getRotation, setRotation } from '@/components/image-viewer/stitchPoints';
import { getWorkspaceGreyscaleUrl } from '@/components/image-viewer/workspace';
import { appState } from '@/lib/appState';
import { computed, onMounted, ref } from 'vue';

const workspace = computed(() => appState.workspace);

const selectedGreyscale = ref<number | null>(0);


function selectGreyscale(idx: number) {
  selectedGreyscale.value = idx;

  // Notify the mapping viewer so it can highlight / enable editing
  window.dispatchEvent(
    new CustomEvent("stitch:selected-grayscale", { detail: idx })
  );
}

onMounted(() => {
  if (selectedGreyscale.value !== null) {
    window.dispatchEvent(
      new CustomEvent("stitch:selected-grayscale", { detail: selectedGreyscale.value })
    );
  }
});

</script>

<template>
 <Window title="Stitching" location="right">
    <div class="space-y-4 p-4">

      <h3 class="font-semibold text-lg">Select a Fragment</h3>

      <div class="grid grid-cols-2 gap-4">
        <div
          v-for="(greyscale, idx) in workspace?.grayscale"
          :key="idx"
          class="cursor-pointer border rounded-md overflow-hidden transition"
          :class="{
            'ring-4 ring-blue-500': selectedGreyscale === idx,
            'hover:ring-2 hover:ring-blue-300': selectedGreyscale !== idx
          }"
          @click="selectGreyscale(idx)"
        >
          <div class="w-full h-32 bg-gray-100 dark:bg-black flex items-center justify-center pt-4">
            <img
              class="max-h-full max-w-full object-contain"
              :src="getWorkspaceGreyscaleUrl(
                greyscale.imageLocation
              )"
              :alt="`Greyscale ${greyscale.sourceCubeName}`"
            />
          </div>
          <div class="text-center text-sm p-1 bg-gray-50 dark:bg-black dark:text-gray-200">
            {{ greyscale.sourceCubeName }}
          </div>
          <div class="mt-2 p-2 border rounded-md">
            <LabeledSlider
              label="Rotation"
              :modelValue="[getRotation(idx)]"
              :min="-180"
              :max="180"
              :step="90"
              @update:modelValue="(val: number[]) => setRotation(idx, val[0])"
            />
          </div>
        </div>
      </div>
    </div>
  </Window>
</template>