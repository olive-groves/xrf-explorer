<script setup lang="ts">
import { Button } from '@/components/ui/button';
import { LabeledSlider } from "@/components/ui/slider";
import { appState } from '@/lib/appState';
import { ref, computed, onMounted, onBeforeUnmount} from "vue";
import { windowState } from "@/components/ui/window/state";
import { getWorkspaceImageUrl } from "@/components/image-viewer/workspace";
import { getRotation, setRotation } from "@/components/image-viewer/stitchPoints";

const selectedGreyscale = ref<number | null>(0);
const mode = ref<'edit' | 'preview'>('edit'); 
const workspace = computed(() => appState.workspace);
interface GreyscaleState {
    opacity: number[];
    xOffset: number[];
    yOffset: number[];
}

const scalingFactor = ref([1.0])

const baseImageOpacity = ref([1.0]);

const GreyscaleMapping = ref<GreyscaleState>(   
    {
        opacity: [1.0],
        xOffset: [0],
        yOffset: [0],
    }
);

const showDialog = ref(false);
const showConfirmation = ref(false);

onMounted(() => {
  if (selectedGreyscale.value !== null) {
    window.dispatchEvent(
      new CustomEvent("stitch:selected-grayscale", { detail: selectedGreyscale.value })
    );
  }
});

function closeDialog() {
  showDialog.value = false;
  showConfirmation.value = false;
}

function confirmStitchingDialog() {
  if (appState.workspace) appState.workspace.stitchingMode = 'full';
      windowState["stitching"].opened = false;
      windowState["stitching"].disabled = true;
}

function onModeChanged(e: Event | CustomEvent) {
  const newMode = (e as CustomEvent).detail as 'edit' | 'preview';
  mode.value = newMode;
}

// Function to adjust the X-offset by a pixel delta (+1 or -1)
function nudgeX(delta: number) {
  window.dispatchEvent(
    new CustomEvent("stitch:gray-nudge", { detail: { dx: delta, dy: 0 } })
  );
}

// Function to adjust the Y-offset by a pixel delta (+1 or -1)
function nudgeY(delta: number) {
  window.dispatchEvent(
    new CustomEvent("stitch:gray-nudge", { detail: { dx: 0, dy: delta } })
  );
}

function updateSliderBase(val: number[]) {
  baseImageOpacity.value = val;
  // Notify preview viwer about the base opacity change
  try {
    const v = Array.isArray(val) ? val[0] : val;
    window.dispatchEvent(new CustomEvent('stitch:base-opacity-changed', { detail: v }));
  } catch (e) {
    console.warn('Could not dispatch stitch base-opacity event', e);
  }
}

function updateGreyscaleOpacity(val: number[]) {
  GreyscaleMapping.value.opacity = val;

  const opacity = val[0];
  window.dispatchEvent(
    new CustomEvent("stitch:gray-opacity-changed", { detail: opacity })
  );
}

function resetGreyscaleOffset() {
  window.dispatchEvent(
    new CustomEvent("stitch:reset-offset")
  );
}


onMounted(() => {
  window.addEventListener('stitchViewer:modeChanged', onModeChanged as EventListener);
});

onBeforeUnmount(() => {
  window.removeEventListener('stitchViewer:modeChanged', onModeChanged as EventListener);
});

function selectGreyscale(idx: number) {
  selectedGreyscale.value = idx;

  // Notify the mapping viewer so it can highlight / enable editing
  window.dispatchEvent(
    new CustomEvent("stitch:selected-grayscale", { detail: idx })
  );
}

// Placeholders for now
const percentagePlaceholders = ref<number[]>([80, 75, 90]); // Example
const estimatedSize = ref(12.5); // GB placeholder
const originalSize = ref(20.0); // GB placeholder

</script>

<template>
  <Window v-if="mode === 'preview'" title="Stitching" location="right">
    <div class="space-y-2 p-2">
      <LabeledSlider
        label="Base Image Opacity"
        :modelValue="baseImageOpacity"
        :min="0.25"
        :max="1"
        :step="0.01"
        @update:modelValue="updateSliderBase"
      />

      <h4 class="font-semibold">{{ `Mapped Data Greyscale` }}</h4>

      <LabeledSlider
        label="Opacity"
        :modelValue="GreyscaleMapping?.opacity ?? [1]"
        :min="0"
        :max="1"
        :step="0.01"
        @update:modelValue="val => updateGreyscaleOpacity(val)"
      />

      <div class="space-y-1">
          <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">X-Offset (pixels)</label>
          <div class="flex items-center space-x-2">
              <Button size="sm" @click="nudgeX(-1)">Left</Button>
              <div class="w-12 text-center font-mono">{{ 0 }}</div>
              <Button size="sm" @click="nudgeX(1)">Right</Button>
          </div>
      </div>

      <!-- X offset displayed and adjustable via nudge buttons (viewer dragging will update this) -->

      <div class="space-y-1">
          <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">Y-Offset (pixels)</label>
          <div class="flex items-center space-x-2">
              <Button size="sm" @click="nudgeY(-1)">Up</Button>
              <div class="w-12 text-center font-mono">{{ 0 }}</div>
              <Button size="sm" @click="nudgeY(1)">Down</Button>
          </div>
      </div>
      <div class="space-y-1">
        <div class="flex items-center space-x-2">
          <Button size="sm" @click="resetGreyscaleOffset">
            Reset offset
          </Button>
        </div>
      </div>

      <LabeledSlider
        label="Scaling Factor"
        :modelValue="scalingFactor"
        :min="0.25"
        :max="2"
        :step="0.01"
      />

      <div class="space-y-1">
        <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
          Reset to recommended scaling factor
        </label>
        <div class="flex items-center space-x-2">
          <Button size="sm" @click="resetGreyscaleOffset">
            Reset scaling
          </Button>
        </div>
      </div>

      <div class="space-y-1 p-2 bg-gray-50 dark:bg-gray-900 rounded-md mt-2 text-sm">
        <div>
          <strong>Percentage remaining quality of datacubes: </strong>
          <span>{{ percentagePlaceholders.join(', ') }}</span>
        </div>
        <div>
          <strong>Estimated stitched datacube size: </strong>
          <span>{{ estimatedSize }} GB</span>
        </div>
        <div>
          <strong>Original file size sum with overlap: </strong>
          <span>{{ originalSize }} GB</span>
        </div>
      </div>
      
      <Button
        variant="outline"
        class="row-span-3 size-full p-2"
        @click="showConfirmation = true"
      >
      Confirm Stitching
      </Button>

      <div v-if="showConfirmation" class="dialog-overlay">
        <div class="dialog-content">
       <h3 class="dialog-title">Confirm Stitching</h3>
       <Button @click="confirmStitchingDialog">Confirm</Button>
       <Button @click="closeDialog">Cancel</Button>
       </div>
      </div>
    </div>
  </Window>
  <Window v-if="mode === 'edit'" title="Stitching" location="right">
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
              :src="getWorkspaceImageUrl(greyscale.imageLocation, workspace?.name)"
              class="max-h-full max-w-full object-contain"
            />
          </div>
          <div class="text-center text-sm p-1 bg-gray-50 dark:bg-black dark:text-gray-200">
            {{ greyscale.name.replace(/^grayscale_/, "") }}
          </div>
          <div class="mt-2 p-2 border rounded-md">
            <LabeledSlider
              label="Rotation"
              :modelValue="[getRotation(idx)]"
              :min="-180"
              :max="180"
              :step="90"
              @update:modelValue="val => setRotation(idx, val[0])"
            />
          </div>
        </div>
      </div>

    </div>
  </Window>
</template>

<style scoped>
.dialog-overlay {
  text-align: center;
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex; align-items: center; justify-content: center;
}
.dialog-content {
  text-align: center;
  background: #fff; padding: 2em; border-radius: 8px;
  display: flex;       
  gap: 20px;              
  justify-content: center; 
  align-items: center;  
}
</style>