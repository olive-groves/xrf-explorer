<script setup lang="ts">
import { Button } from '@/components/ui/button';
import { LabeledSlider } from "@/components/ui/slider";
import { appState } from '@/lib/appState';
import { ref, computed, watch, onMounted, onBeforeUnmount, inject, Ref } from "vue";
import { windowState } from "@/components/ui/window/state";
import { getWorkspaceImageUrl } from "@/components/image-viewer/workspace";
import { getRotation, setRotation } from "@/components/image-viewer/stitchPoints";

const selectedGreyscale = ref<number | null>(0);
const mode = inject<Ref<'edit' | 'preview'>>("stitchMode", ref('edit'));
const workspace = computed(() => appState.workspace);
interface PartialScanState {
    opacity: number[];
    xOffset: number[];
    yOffset: number[];
    rotation: number[];
}

const baseImageOpacity = ref([1.0]);

const partialScans = ref<PartialScanState[]>([    
    {
        opacity: [1.0],
        xOffset: [0],
        yOffset: [0],
        rotation: [0],
    }
]);


onMounted(() => {
  if (selectedGreyscale.value !== null) {
    window.dispatchEvent(
      new CustomEvent("stitch:selected-grayscale", { detail: selectedGreyscale.value })
    );
  }
});

// Keep partialScans in sync with workspace grayscale count so each slider has a model
watch(
  () => workspace.value?.grayscale,
  (g: any) => {
    const n = (g && g.length) || 0;
    // add missing entries
    while (partialScans.value.length < n) {
      partialScans.value.push({ opacity: [1.0], xOffset: [0], yOffset: [0], rotation: [0] });
    }
    // trim extra entries
    if (partialScans.value.length > n) partialScans.value.splice(n);
  },
  { immediate: true }
);
const showDialog = ref(false);
const showConfirmation = ref(false);

function closeDialog() {
  showDialog.value = false;
  showConfirmation.value = false;
}

function confirmDialog() {
    partialScans.value.push({
        opacity: [1.0],
        xOffset: [0],
        yOffset: [0],
        rotation: [0],
    });
    closeDialog();
}

function confirmStitchingDialog() {
  if (appState.workspace) appState.workspace.stitchingMode = 'full';
      windowState["stitching"].opened = false;
      windowState["stitching"].disabled = true;
}

function updatePartialScan(idx: number, prop: keyof PartialScanState, val: number[]) {
    // Normalize rotation updates to 90-degree steps and clamp to [-180,180]
    if (prop === 'rotation') {
      const raw = Number(Array.isArray(val) ? val[0] : val);
      const snapped = Math.round(raw / 90) * 90;
      const clamped = Math.max(-180, Math.min(180, snapped));
      partialScans.value[idx][prop] = [clamped];
      try {
        window.dispatchEvent(new CustomEvent('stitch:grayscale-prop-changed', { detail: { index: idx, prop, value: clamped } }));
      } catch (e) {
        console.warn('Could not dispatch grayscale prop change', e);
      }
      return;
    }
    partialScans.value[idx][prop] = val;
    // no special-case forwarding here; use per-index events so each slider maps to its greyscale
    // Dispatch a generic per-index property change so the StitchViewer can react
    try {
      const numeric = Array.isArray(val) ? Number(val[0]) : Number(val);
      window.dispatchEvent(new CustomEvent('stitch:grayscale-prop-changed', { detail: { index: idx, prop, value: numeric } }));
    } catch (e) {
      console.warn('Could not dispatch grayscale prop change', e);
    }
}

// Function to adjust the X-offset by a pixel delta (+1 or -1)
function nudgeX(idx: number, delta: number) {
  const cur = partialScans.value[idx].xOffset ?? [0];
  const next = [ (cur[0] ?? 0) + delta ];
  updatePartialScan(idx, 'xOffset', next);
}

// Function to adjust the Y-offset by a pixel delta (+1 or -1)
function nudgeY(idx: number, delta: number) {
  const cur = partialScans.value[idx].yOffset ?? [0];
  const next = [ (cur[0] ?? 0) + delta ];
  updatePartialScan(idx, 'yOffset', next);
}

function updateSliderBase(val: number[]) {
  baseImageOpacity.value = val;
  // Notify other components (e.g. StitchViewer) about the base opacity change
  try {
    const v = Array.isArray(val) ? val[0] : val;
    window.dispatchEvent(new CustomEvent('stitch:base-opacity-changed', { detail: v }));
  } catch (e) {
    console.warn('Could not dispatch stitch base-opacity event', e);
  }
}

function onGrayscalePosChanged(e: Event | CustomEvent) {
  try {
    const d = (e as CustomEvent).detail;
    if (!d) return;
    const { index, x, y } = d as { index: number; x: number; y: number };
    // update local display state but do not re-dispatch (viewer is authoritative while dragging)
    if (partialScans.value[index]) {
      partialScans.value[index].xOffset = [Number(x)];
      partialScans.value[index].yOffset = [Number(y)];
    }
  } catch (err) {
    console.warn('Error handling grayscale pos changed', err);
  }
}

function selectGreyscale(idx: number) {
  selectedGreyscale.value = idx;

  // Notify the mapping viewer so it can highlight / enable editing
  window.dispatchEvent(
    new CustomEvent("stitch:selected-grayscale", { detail: idx })
  );
}

onMounted(() => {
  window.addEventListener('stitch:grayscale-pos-changed', onGrayscalePosChanged as EventListener);
  // listen for rotation changes originating from the viewer (so the slider display updates)
  window.addEventListener('stitch:grayscale-prop-changed', onGrayscalePropFromViewer as EventListener);
});

onBeforeUnmount(() => {
  window.removeEventListener('stitch:grayscale-pos-changed', onGrayscalePosChanged as EventListener);
  window.removeEventListener('stitch:grayscale-prop-changed', onGrayscalePropFromViewer as EventListener);
});

function onGrayscalePropFromViewer(e: Event | CustomEvent) {
  try {
    const d = (e as CustomEvent).detail;
    if (!d) return;
    const { index, prop, value } = d as { index: number; prop: string; value: number };
    if (prop !== 'rotation') return; // only handle rotation here
    if (!partialScans.value[index]) return;
    // update local rotation display without re-dispatching
    partialScans.value[index].rotation = [Number(value)];
  } catch (err) {
    console.warn('Error handling grayscale prop from viewer', err);
  }
}

// no selected-grayscale slider here; Partial Scan 1 slider forwards to the viewer directly

</script>

<template>
  <Window v-if="mode === 'preview'" title="Stitching" location="right">
    <div class="space-y-2 p-2">
      <Button
        variant="outline"
        class="w-full p-2"
        @click="showDialog = true"
        >
        Add Parts
      </Button>
      <LabeledSlider
        label="Base Image Opacity"
        :modelValue="baseImageOpacity"
        :min="0.25"
        :max="1"
        :step="0.01"
        @update:modelValue="updateSliderBase"
      />

      <div v-for="(greyscale, idx) in workspace?.grayscale" :key="idx" class="border p-2 rounded-md space-y-2">
        <h4 class="font-semibold">{{ `Partial Scan ${greyscale.name}` }}</h4>

        <LabeledSlider
          label="Opacity"
          :modelValue="partialScans[idx]?.opacity ?? [1]"
          :min="0"
          :max="1"
          :step="0.01"
          @update:modelValue="val => updatePartialScan(idx, 'opacity', val)"
        />

        <div class="space-y-1">
            <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">X-Offset (pixels)</label>
            <div class="flex items-center space-x-2">
                <Button size="sm" @click="nudgeX(idx, -1)">Left</Button>
                <div class="w-12 text-center font-mono">{{ partialScans[idx]?.xOffset?.[0] ?? 0 }}</div>
                <Button size="sm" @click="nudgeX(idx, 1)">Right</Button>
            </div>
        </div>

        <!-- X offset displayed and adjustable via nudge buttons (viewer dragging will update this) -->

        <div class="space-y-1">
            <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">Y-Offset (pixels)</label>
            <div class="flex items-center space-x-2">
                <Button size="sm" @click="nudgeY(idx, -1)">Up</Button>
                <div class="w-12 text-center font-mono">{{ partialScans[idx]?.yOffset?.[0] ?? 0 }}</div>
                <Button size="sm" @click="nudgeY(idx, 1)">Down</Button>
            </div>
        </div>
      </div>
      
      <Button
        variant="outline"
        class="row-span-3 size-full p-2"
        @click="showConfirmation = true"
      >
      Confirm Stitching
      </Button>

      <div v-if="showDialog" class="dialog-overlay">
        <div class="dialog-content">
        <h3 class="dialog-title">Add parts</h3>
        <Button @click="">Upload Fragment</Button>
        <Button @click="confirmDialog">Confirm</Button>
        <Button @click="closeDialog">Cancel</Button>
        </div>
        </div>
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