<script setup lang="ts">
import { elementalDataPresent } from "@/lib/appState";
import { Window } from "@/components/ui/window";
import { LoaderPinwheel, Trash2, Calculator } from "lucide-vue-next";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
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
  segmentationMode,
  elementsSelected,
  selectableElementsList,
  disabledElements,
  recommendedClusters,

  // Methods
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
      <!-- MODE TOGGLE -->
      <div class="flex w-full rounded-md bg-muted p-1">
        <Button
          class="flex-1"
          :variant="segmentationMode === 'complete' ? 'default' : 'ghost'"
          @click="segmentationMode = 'complete'"
        >
          Complete Painting
        </Button>
        <Button
          class="flex-1"
          :variant="segmentationMode === 'elements' ? 'default' : 'ghost'"
          @click="segmentationMode = 'elements'"
        >
          Elements
        </Button>
      </div>

      <!-- USE SELECTION AREA CHECKBOX -->
      <div class="flex items-center space-x-2 pt-2">
        <Checkbox id="use_selection_area" class="align-bottom" v-model:checked="useSelectionChecked" />
        <Label for="use_selection_area" class="align-middle">Use only selection area</Label>
      </div>

      <!-- ELEMENT SELECTION (Only shown in Elements mode) -->
      <div v-if="segmentationMode === 'elements'" class="mt-2 space-y-2 border-t pt-2">
        <div class="flex items-center space-x-4" v-for="(elementSel, index) in elementsSelected" :key="elementSel.id">
          <div class="max-w-36 grow space-y-1">
            <Label v-if="index === 0" for="element">Element</Label>
            <Select v-model="elementSel.name" class="w-full">
              <SelectTrigger>
                <SelectValue placeholder="Select element" />
              </SelectTrigger>
              <SelectContent>
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
            <Label v-if="index === 0" for="elemental_threshold">Threshold (%)</Label>
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
              :class="index === 0 ? 'mt-6 p-2' : 'p-2'"
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
          :disabled="elementsSelected.length >= selectableElementsList.length"
        >
          Add element
        </Button>
      </div>

      <!-- RECOMMENDED CLUSTERS -->
      <div class="border-t border-border pt-2">
        <Label for="recommendClusters" class="block pb-2">Recommended Amount of Clusters:</Label>
        <div class="flex w-full flex-nowrap space-x-2">
          <div class="w-auto space-y-1">
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
          <Button @click="calculateRecommendedClusters">
            <Calculator class="size-4" />
          </Button>
          <Button
            :disabled="recommendedStatus !== Status.SUCCESS"
            @click="setRecommendedClusters"
          >
            <template v-if="recommendedStatus === Status.LOADING"> Loading... </template>
            <template v-else> Use ({{ recommendedClusters || "-" }}) </template>
          </Button>
        </div>
      </div>

      <!-- COLOR CLUSTER GENERATION -->
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
      <div v-if="status == Status.SUCCESS" class="flex flex-wrap gap-2">
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
  </Window>
</template>