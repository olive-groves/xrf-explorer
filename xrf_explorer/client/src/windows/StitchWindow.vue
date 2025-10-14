<script setup lang="ts">
import { Button } from '@/components/ui/button';
import { Dialog, DialogTrigger } from "@/components/ui/dialog";
import { LabeledSlider } from "@/components/ui/slider";
import { appState } from '@/lib/appState';
import { ref } from "vue";

const baseImageOpacity = ref([1.0]);
const partialOpacities = ref<number[][]>([[1.0]]);
const showDialog = ref(false);
const showConfirmation = ref(false);

// Close a dialog
function closeDialog() {
  showDialog.value = false;
  showConfirmation.value = false;
}

// Function to confirm add parts dialog
function confirmDialog() {
    partialOpacities.value.push([1.0])
    closeDialog();
}

// Close the stitching page and load the base-RGB viewer with the base image and datacubes
function confirmStitchingDialog() {
       appState.stitching = false;
       // Load base image etc.
}

// Slider used for the partial scans
function updateSlider(idx: number, val: number[]) {
  partialOpacities.value[idx] = val;
}

// Slider for the base image
function updateSliderBase(val: number[]) {
  baseImageOpacity.value = val;
}

</script>

<template>
  <Window title="Stitching" location="right">
    <div class="space-y-2 p-2">
      <!-- BUTTON TO ADD PARTS -->
      <Button
        variant="outline"
        class="row-span-3 size-full p-2"
        @click="showDialog = true"      
      >
      <p>Add parts</p>
      </Button>

      <!-- BASE IMAGE OPACITY SLIDER  -->
      <LabeledSlider
        label="Base Image Opacity"
        :modelValue="baseImageOpacity"
        :min="0"
        :max="1"
        :step="0.01"
        @update:modelValue="updateSliderBase"></LabeledSlider> 
        
      <!-- SLIDER FOR CURRENT SELECTED PARTIAL SCAN  -->
      <div v-for="(opacity, idx) in partialOpacities" :key="idx">
        <LabeledSlider
        :label="`Partial Scan ${idx + 1}`"
        :modelValue="opacity"
        :min="0"
        :max="1"
        :step="0.01"
        @update:modelValue="val => updateSlider(idx, val)"
        />
    </div>
      
      <!-- BUTTON TO CONFIRM STITCHING -->
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
  flex-direction: column;
  background: #fff; padding: 2em; border-radius: 8px;
  display: flex;       
  gap: 20px;              
  justify-content: center; 
  align-items: center;  
}
</style>