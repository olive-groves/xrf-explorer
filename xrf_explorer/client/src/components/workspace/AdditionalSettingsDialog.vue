<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { Dialog, DialogTrigger, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ref } from "vue";
import { WorkspaceConfig } from "@/lib/workspace";

const model = defineModel<WorkspaceConfig>({ required: true });

const dialogOpen = ref(false);

// Min and max energy for spectra parameters
const MIN_ENERGY = 0;
const MAX_ENERGY = 4096;

const constraints = `Parameters must respect ${MIN_ENERGY} ≤ low < high ≤ ${MAX_ENERGY}, 0 < bin size ≤ high - low`;

/**
 * Updates the state of the dialog.
 * @param open - The new state the dialog is requested to have.
 */
function dialogUpdate(open: boolean) {
  dialogOpen.value = open;
}

//temporary variables to store parameters before save
const low = ref(model.value.spectralParams.low);
const high = ref(model.value.spectralParams.high);
const binSize = ref(model.value.spectralParams.binSize);
const offset = ref(model.value.spectralParams.offset); // Corrected variable name from mode.value to model.value
const correctSpectraParams = ref(true);

/**
 * Check if entered parameters satisfy the constraints.
 */
function updateCorrectParams() {
  if (
    MIN_ENERGY <= low.value &&
    low.value < MAX_ENERGY &&
    MIN_ENERGY < high.value &&
    high.value <= MAX_ENERGY &&
    0 < binSize.value &&
    binSize.value <= high.value - low.value
  ) {
    correctSpectraParams.value = true;
  } else {
    correctSpectraParams.value = false;
  }
}

/**
 * Save entered values to the model and close dialog.
 */
function save() {
  model.value.spectralParams.low = low.value;
  model.value.spectralParams.high = high.value;
  model.value.spectralParams.binSize = binSize.value;
  model.value.spectralParams.offset = offset.value;
  dialogOpen.value = false;
}
</script>

<template>
  <Dialog :open="dialogOpen" @update:open="dialogUpdate">
    <DialogTrigger>
      <Button variant="outline">Additional settings</Button>
    </DialogTrigger>
    <DialogContent>
      <div class="space-y-4">
        <DialogTitle class="font-bold">Additional settings</DialogTitle>

        <p class="font-bold">Spectral datacube parameters</p>
        <Label>{{ constraints }}</Label>

        <div class="flex space-x-4">
          <div class="flex-1 space-y-2">
            <Label for="low-input">Lower energy boundary (channels)</Label>
            <Input
              ref="inputComponent"
              type="number"
              :min="MIN_ENERGY"
              :max="MAX_ENERGY"
              step="1"
              v-model="low"
              id="low-input"
              @change="updateCorrectParams"
            />
          </div>

          <div class="flex-1 space-y-2">
            <Label for="high-input">Higher energy boundary (channels)</Label>
            <Input
              ref="inputComponent"
              type="number"
              step="1"
              :min="MIN_ENERGY"
              :max="MAX_ENERGY"
              v-model="high"
              id="high-input"
              @change="updateCorrectParams"
            />
          </div>
        </div>

        <div class="flex space-x-4">
          <div class="flex-1 space-y-2">
            <Label for="bin-size-input">Bin size (channels)</Label>
            <Input
              ref="inputComponent"
              type="number"
              min="0"
              :max="MAX_ENERGY"
              step="1"
              v-model="binSize"
              id="bin-size-input"
              @change="updateCorrectParams"
            />
          </div>

          <div class="flex-1 space-y-2">
            <Label for="offset-input">Offset (KeV)</Label>
            <Input
              ref="inputComponent"
              type="number"
              step="1"
              min="0"
              :max="MAX_ENERGY"
              v-model="offset"
              id="offset-input"
              @change="updateCorrectParams"
            />
          </div>
        </div>

        <Button :disabled="!correctSpectraParams" @click="save" title="save-params">Save</Button>
        <Label style="color: red" v-show="!correctSpectraParams"> Parameters do not meet constraints</Label>
      </div>
    </DialogContent>
  </Dialog>
</template>
