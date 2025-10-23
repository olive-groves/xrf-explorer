<script setup lang="ts">
import { Button } from '@/components/ui/button';
import { LabeledSlider } from "@/components/ui/slider";
import { appState } from '@/lib/appState';
import { ref } from "vue";
import { windowState } from "@/components/ui/window/state";
// no lifecycle imports needed

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
    partialScans.value[idx][prop] = val;
    // If the first partial scan opacity changed, forward it to the selected grayscale
    if (idx === 0 && prop === 'opacity') {
      try {
        const v = Array.isArray(val) ? val[0] : val;
        window.dispatchEvent(new CustomEvent('stitch:selected-grayscale-opacity-changed', { detail: v }));
      } catch (e) {
        console.warn('Could not dispatch selected grayscale opacity from partial scan', e);
      }
    }
}

// Function to adjust the X-offset by a pixel delta (+1 or -1)
function nudgeX(idx: number, delta: number) {
    partialScans.value[idx].xOffset[0] += delta;
}

// Function to adjust the Y-offset by a pixel delta (+1 or -1)
function nudgeY(idx: number, delta: number) {
    partialScans.value[idx].yOffset[0] += delta;
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

// no selected-grayscale slider here; Partial Scan 1 slider forwards to the viewer directly

</script>

<template>
  <Window title="Stitching" location="right">
    <div class="space-y-2 p-2">
      <Button
        variant="outline"
        class="row-span-3 size-full p-2"
        @click="showDialog = true"
      >
      <p>Add parts</p>
      </Button>

      <LabeledSlider
        label="Base Image Opacity"
        :modelValue="baseImageOpacity"
        :min="0"
        :max="1"
        :step="0.01"
        @update:modelValue="updateSliderBase"
      />

      <div v-for="(scan, idx) in partialScans" :key="idx" class="border p-2 rounded-md space-y-2">
        <h4 class="font-semibold">{{ `Partial Scan ${idx + 1}` }}</h4>

        <LabeledSlider
          label="Opacity"
          :modelValue="scan.opacity"
          :min="0"
          :max="1"
          :step="0.01"
          @update:modelValue="val => updatePartialScan(idx, 'opacity', val)"
        />

        <div class="space-y-1">
            <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">X-Offset (pixels)</label>
            <div class="flex items-center space-x-2">
                <Button size="sm" @click="nudgeX(idx, -1)">Left</Button>
                <div class="w-12 text-center font-mono"></div>
                <Button size="sm" @click="nudgeX(idx, 1)">Right</Button>
            </div>
        </div>

        <div class="space-y-1">
            <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">Y-Offset (pixels)</label>
            <div class="flex items-center space-x-2">
                <Button size="sm" @click="nudgeY(idx, -1)">Up</Button>
                <div class="w-12 text-center font-mono"></div>
                <Button size="sm" @click="nudgeY(idx, 1)">Down</Button>
            </div>
        </div>
        
        <LabeledSlider
          label="Rotation (degrees)"
          :modelValue="scan.rotation"
          :min="-180" 
          :max="180" 
          :step="0.1"
          @update:modelValue="val => updatePartialScan(idx, 'rotation', val)"
        />
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