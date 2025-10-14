<script setup lang="ts">
import { computed, ComputedRef, inject, ref, watch } from "vue";
import { appState, datasource, elementalDataPresent, elements } from "@/lib/appState";
import { Window } from "@/components/ui/window";
import { LoaderPinwheel } from "lucide-vue-next";
import { FrontendConfig } from "@/lib/config";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "vue-sonner";
import {
  NumberField,
  NumberFieldContent,
  NumberFieldDecrement,
  NumberFieldIncrement,
  NumberFieldInput,
} from "@/components/ui/number-field";
import { getTargetSize } from "@/components/image-viewer/api.ts";
import { SelectionAreaSelection, SelectionAreaType } from "@/lib/selection.ts";
import {
  areSelectionAreaSelectionsEqual,
  deepClone,
  flipSelectionAreaSelection,
  hasActiveSelection,
} from "@/lib/utils.ts";

// Custom type for keeping track of what selection to use.
type ColorSegmentationAreaSelection = {
  areaSelection: SelectionAreaSelection;
  lastChangedTimestamp: number;
};

// Constants and injected values
const config = inject<FrontendConfig>("config")!;

// Enum declarations
enum Status {
  WAITING,
  LOADING,
  ERROR,
  SUCCESS,
}

// Reactive variables
const colors = ref<string[]>([""]);
const selectedElement = ref<string>();
const useSelectionChecked = ref<boolean>(false);
const threshold = ref(20);
const number_clusters = ref(10);
const currentError = ref("Unknown error");
const status = ref(Status.WAITING);

// Computed properties
const selection = computed(() => appState.selection.colorSegmentation);
const areaSelection: ComputedRef<SelectionAreaSelection> = computed(() => appState.selection.imageViewer);

// Non-reactive variables
const currentAreaSelection: ColorSegmentationAreaSelection = {
  areaSelection: {
    type: SelectionAreaType.Rectangle,
    points: [
      { x: 0, y: 0 },
      { x: 10000, y: 10000 },
    ],
  },
  lastChangedTimestamp: Date.now(),
};

// Watchers
watch(areaSelection, updateAreaSelection, { deep: true, immediate: true });

/**
 * Fetch the hexadecimal colors' data.
 * @returns True if the colors were fetched successfully, false otherwise.
 */
async function fetchColors() {
  status.value = Status.LOADING;
  if (selectedElement.value == null) {
    currentError.value = "Please select an element";
    status.value = Status.ERROR;
    return;
  }

  let request_body: SelectionAreaSelection;

  if (useSelectionChecked.value) {
    request_body = flipSelectionAreaSelection(currentAreaSelection.areaSelection, (await getTargetSize()).height);
  } else {
    request_body = await getFullImageSelection();
  }

  const elementIndex = getElementIndex(selectedElement.value);
  const response = await fetch(
    `${config.api.endpoint}/${datasource.value}/cs/clusters/` +
      `/${elementIndex}/${number_clusters.value}/${threshold.value}/${useSelectionChecked.value}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request_body),
    },
  );

  if (!response.ok) {
    toast.warning("Failed to retrieve colors");
    currentError.value = "Failed to retrieve or generate color clusters";
    status.value = Status.ERROR;
    return false;
  }

  colors.value = await response.json();
  return true;
}

/**
 * Generates color clusters based on the user-set parameters,
 * and updates the CS selection.
 */
async function generateColors() {
  try {
    // Whether the colors were fetched properly
    await fetchColors();
  } catch (e) {
    status.value = Status.ERROR;
    toast.warning("Failed to retrieve painting colors");
    console.error("Error fetching colors data", e);
    return;
  }
  status.value = Status.SUCCESS;

  updateSelection();
}

/**
 * Sets the CS selection.
 */
function updateSelection() {
  const elementIndex = getElementIndex(selectedElement.value);

  if (selection.value != undefined) {
    // Update selection
    selection.value.element = elementIndex;
    selection.value.enabled = Array(colors.value.length).fill(false);
    selection.value.colors = colors.value;
    selection.value.k = number_clusters.value;
    selection.value.threshold = threshold.value;
    selection.value.useAreaSelection = useSelectionChecked.value;
    selection.value.areaSelection = deepClone(currentAreaSelection.areaSelection);
    selection.value.lastCompleteSelectionTimestamp = currentAreaSelection.lastChangedTimestamp;
  }
}

/**
 * Updates the currentAreaSelection if the new Selection made by the user is a new one, and valid.
 * @param newSelection The new selection made by the user.
 */
function updateAreaSelection(newSelection: SelectionAreaSelection) {
  if (
    hasActiveSelection(newSelection) &&
    !areSelectionAreaSelectionsEqual(newSelection, currentAreaSelection.areaSelection)
  ) {
    currentAreaSelection.areaSelection = deepClone(newSelection);
    currentAreaSelection.lastChangedTimestamp = Date.now();
  }
}

/**
 * Toggles (enables/disables) the given color cluster.
 * @param colorIndex The index of the selected cluster/color.
 */
function toggleCluster(colorIndex: number) {
  if (selection.value.enabled[colorIndex] != undefined) {
    selection.value.enabled[colorIndex] = !selection.value.enabled[colorIndex];
  }
}

/**
 * Returns the index of the given element/complete painting to pass to the backend,
 * by setting the complete painting to index 0, and
 * the elements to their channel number plus 1.
 * @param elementName Name of element/complete painting to get index of.
 * @returns Index of the element/complete painting.
 */
function getElementIndex(elementName: string | undefined) {
  if (elementName == undefined) {
    return 0;
  }
  // Get index of new channel
  if (elementName == "complete") {
    return 0;
  } else {
    const index = elements.value.findIndex((element) => element.name === elementName);
    return elements.value[index].channel + 1;
  }
}

/**
 * Returns a selection object that exactly covers the entire painting.
 * @returns A `SelectionAreaSelection` object exactly covering the entire painting.
 */
async function getFullImageSelection(): Promise<SelectionAreaSelection> {
  const size = await getTargetSize();
  return {
    type: SelectionAreaType.Rectangle,
    points: [
      { x: 0, y: 0 },
      { x: size.width, y: size.height },
    ],
  };
}
</script>

<template>
  <Window title="Color segmentation" location="right" :disabled="!elementalDataPresent">
    <div class="space-y-2 p-2">
      <!-- USE SELECTION AREA CHECKBOX -->
      <div class="flex items-center space-x-2">
        <Checkbox id="use_selection_area" v-model:checked="useSelectionChecked" />
        <Label for="use_selection_area">Use only selection area</Label>
      </div>

      <!-- COLOR CLUSTER GENERATION -->
      <div class="flex space-x-2">
        <!-- ELEMENT SELECTION -->
        <div class="grow space-y-1">
          <Label for="element">Element</Label>
          <Select v-model="selectedElement" class="w-full">
            <SelectTrigger>
              <SelectValue placeholder="Select an element" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="complete"> Complete painting </SelectItem>
              <SelectItem v-for="element in elements" :key="element.name" :value="element.name">
                {{ element.name }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      <!-- PARAMETER SELECTION -->
      <div class="flex items-center space-x-4">
        <div class="flex-1 space-y-1">
          <Label for="elemental_threshold">Threshold (%)</Label>
          <NumberField
            v-model="threshold"
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
        <div class="flex-1 space-y-1">
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
      <div v-if="selectedElement && status == Status.SUCCESS" class="flex flex-wrap gap-2">
        <div
          v-for="(color, colorIndex) in colors"
          :key="color"
          :style="{ 'background-color': color }"
          class="inline-block size-12 rounded-md"
          :class="{
            'ring-2 ring-foreground ring-offset-1 ring-offset-background': selection.enabled[colorIndex],
          }"
          @click="toggleCluster(colorIndex)"
        />
      </div>
    </div>
  </Window>
</template>
