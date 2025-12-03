<script setup lang="ts">
import { elementalDataPresent } from "@/lib/appState";
import { Window } from "@/components/ui/window";
import { LoaderPinwheel, Trash2 } from "lucide-vue-next";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import {
  NumberField,
  NumberFieldContent,
  NumberFieldDecrement,
  NumberFieldIncrement,
  NumberFieldInput,
} from "@/components/ui/number-field";
import { Checkbox } from "@/components/ui/checkbox";
import { useCSWindow, Status } from "@/windows/CSWindow.ts";

// Using the composable function to manage state and behavior
const {
  recommendedStatus,
  selection,
  number_clusters,
  currentError,
  colors,
  useSelectionChecked,
  status,
  elementsSelected,
  selectableElementsList,
  disabledElements,
  showConfirmDialog,
  recommendedClusters,

  // Methods
  handleConfirm,
  generateColors,
  toggleCluster,
  enableAllClusters,
  disableAllClusters,
  addElementSelection,
  removeElement,
  calculateRecommendedClusters,
  setRecommendedClusters,
} = useCSWindow();
</script>

<template>
  <Window title="Color segmentation" location="right" :disabled="!elementalDataPresent">
    <div class="space-y-2 p-2">
      <!-- USE SELECTION AREA CHECKBOX -->
      <div class="flex items-center space-x-2">
        <Checkbox id="use_selection_area" class="align-bottom" v-model:checked="useSelectionChecked" />
        <Label for="use_selection_area" class="align-middle">Use only selection area</Label>
      </div>
      <!-- ELEMENT SELECTION -->
      <div class="flex items-center space-x-4" v-for="(elementSel, index) in elementsSelected" :key="elementSel.id">
        <div class="max-w-36 grow space-y-1">
          <Label for="element">Element</Label>
          <Select v-model="elementSel.name" class="w-full">
            <SelectTrigger>
              <SelectValue placeholder="Select element" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="complete" :disabled="elementsSelected.some((sel) => sel.name === 'complete')">
                Complete painting
              </SelectItem>
              <SelectItem
                v-for="element in selectableElementsList"
                :key="element.name"
                :value="element.name"
                :disabled="disabledElements.includes(element.name) && elementSel.name !== element.name"
              >
                {{ element.name }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div class="flex-1 space-y-1">
          <Label for="elemental_threshold">Threshold (%)</Label>
          <NumberField
            v-model="elementSel.threshold"
            :min="0"
            :max="100"
            :step="1"
            id="elemental_threshold"
            :format-options="{
              minimumIntegerDigits: 1,
              maximumFractionDigits: 0,
            }"
          >
            <NumberFieldContent>
              <NumberFieldDecrement />
              <NumberFieldInput />
              <NumberFieldIncrement />
            </NumberFieldContent>
          </NumberField>
        </div>
        <div>
          <Button
            variant="destructive"
            class="mt-6 p-2"
            @click="removeElement(index)"
            :disabled="elementsSelected.length === 1"
            title="Remove element"
          >
            <Trash2 class="size-4" />
          </Button>
        </div>
      </div>
      <Button
        variant="outline"
        @click="addElementSelection"
        :disabled="
          elementsSelected.length >= selectableElementsList.length ||
          elementsSelected.some((sel) => sel.name === 'complete')
        "
      >
        Add element
      </Button>
      <!-- RECOMMENDED CLUSTERS -->
      <div class="flex flex-col space-y-1.5 border-t border-border pt-2">
        <Label for="recommendClusters">Recommended Amount of Clusters:</Label>
        <div class="flex w-full flex-nowrap space-x-2">
          <div class="min-w-0 basis-2/5 p-1">
            <Button class="size-full whitespace-normal text-center" @click="calculateRecommendedClusters">
              Calculate
            </Button>
          </div>
          <div class="min-w-0 basis-3/5 p-1">
            <Button
              class="size-full whitespace-normal text-center"
              :disabled="recommendedStatus !== Status.SUCCESS"
              @click="setRecommendedClusters"
            >
              <template v-if="recommendedStatus === Status.LOADING"> Loading... </template>
              <template v-else> Use recommended ({{ recommendedClusters || "" }}) </template>
            </Button>
          </div>
        </div>
      </div>
      <!-- COLOR CLUSTER GENERATION -->
      <div class="flex space-x-2">
        <!-- CLUSTER NUMBER SELECTION -->
        <div class="w-auto space-y-1">
          <Label for="number_clusters">Number of clusters (1-50)</Label>
          <NumberField
            v-model="number_clusters"
            :min="1"
            :max="50"
            :step="1"
            id="number_clusters"
            :format-options="{
              minimumIntegerDigits: 1,
              maximumFractionDigits: 0,
            }"
          >
            <NumberFieldContent>
              <NumberFieldDecrement />
              <NumberFieldInput />
              <NumberFieldIncrement />
            </NumberFieldContent>
          </NumberField>
        </div>
      </div>
      <Button class="w-full" @click="generateColors">Generate color clusters</Button>

      <!-- LOADING/ERROR MESSAGES -->
      <div
        class="flex flex-col items-center justify-center space-y-2 p-8"
        v-if="status == Status.LOADING || status == Status.ERROR"
      >
        <span v-if="status == Status.LOADING">Loading...</span>
        <div v-if="status == Status.LOADING" class="size-6">
          <LoaderPinwheel class="size-full animate-spin" />
        </div>
        <span v-if="status == Status.ERROR">{{ currentError }}</span>
      </div>

      <!-- COLOR PALETTE -->
      <div v-if="elementsSelected[0] && status == Status.SUCCESS" class="flex flex-wrap gap-2">
        <div
          v-for="(color, colorIndex) in colors"
          :key="color"
          :style="{ 'background-color': color }"
          class="inline-block size-12 rounded-md"
          :class="{
            'ring-2 ring-offset-1': selection.enabled[colorIndex],
          }"
          @click="toggleCluster(colorIndex)"
        />
      </div>
      <div v-if="status == Status.SUCCESS && colors.length > 0" class="flex w-full gap-2">
        <Button class="basis-1/2" variant="outline" @click="enableAllClusters">Select All</Button>
        <Button class="basis-1/2" variant="outline" @click="disableAllClusters">Deselect All</Button>
      </div>
    </div>
    <Dialog v-model:open="showConfirmDialog">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Confirm Selection</DialogTitle>
          <DialogDescription>
            <div class="mt-3">Selecting 'Complete painting' will remove all other selected elements. Continue?</div>
          </DialogDescription>
        </DialogHeader>
        <div class="mt-1 flex justify-end space-x-2">
          <Button variant="outline" @click="handleConfirm(false)">Cancel</Button>
          <Button @click="handleConfirm(true)">Confirm</Button>
        </div>
      </DialogContent>
    </Dialog>
  </Window>
</template>
