<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { Dialog, DialogTrigger, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ref } from "vue";
import { WorkspaceConfig } from "@/lib/workspace";

const model = defineModel<WorkspaceConfig>({ required: true });

const dialogOpen = ref(false);

const constraints = "Parameters must respect 0 <= low < high <= 40, 0 < bin size <= high - low";

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
const correctSpectraParams = ref(true);

/**
 * Check if entered parameters satisfy the constraints.
 */
function updateCorrectParams() {
  if (
    0 <= low.value &&
    low.value < 40 &&
    0 < high.value &&
    high.value <= 40 &&
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
        <!-- HEADER -->
        <DialogTitle class="font-bold">Additional settings</DialogTitle>

        <!-- Spectra parameters -->
        <p class="font-bold">Spectral datacube parameters</p>
        <Label>{{ constraints }}</Label>
        <div class="space-x-2">
          <Label for="low-input">Lower energy boundary (keV)</Label>
          <Input
            ref="inputComponent"
            type="number"
            min="0"
            max="40"
            step="1"
            v-model="low"
            id="low-input"
            @change="updateCorrectParams"
          />
        </div>
        <div class="space-x-2">
          <Label for="high-input">Higher energy boundary (keV)</Label>
          <Input
            ref="inputComponent"
            type="number"
            step="1"
            min="0"
            max="40"
            v-model="high"
            id="high-input"
            @change="updateCorrectParams"
          />
        </div>
        <div class="space-x-2">
          <Label for="bin-size-input">Bin size (keV)</Label>
          <Input
            ref="inputComponent"
            type="number"
            min="1"
            max="40"
            step="1"
            v-model="binSize"
            id="bin-size-input"
            @change="updateCorrectParams"
          />
        </div>

        <!--Footer-->
        <Button :disabled="!correctSpectraParams" @click="save" title="save-params">Save</Button>
        <Label style="color: red" v-show="!correctSpectraParams"> Parameters do not meet constraints</Label>
      </div>
    </DialogContent>
  </Dialog>
</template>
