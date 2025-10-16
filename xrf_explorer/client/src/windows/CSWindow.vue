<script setup lang="ts">
import { computed, ComputedRef, inject, ref, watch } from "vue";
import { appState, datasource, elementalDataPresent, elements } from "@/lib/appState";
import { Window } from "@/components/ui/window";
import { LoaderPinwheel, Trash2} from "lucide-vue-next";
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

import { Checkbox } from "@/components/ui/checkbox";
import { getTargetSize } from "@/components/image-viewer/api.ts";
import { SelectionAreaSelection, SelectionAreaType } from "@/lib/selection.ts";
import {
  areSelectionAreaSelectionsEqual,
  deepClone,
  flipSelectionAreaSelection,
  hasActiveSelection,
} from "@/lib/utils.ts";

enum Status {
  WAITING,
  LOADING,
  ERROR,
  SUCCESS,
}

// Custom type for keeping track of what selection to use.
type ColorSegmentationAreaSelection = {
  areaSelection: SelectionAreaSelection;
  lastChangedTimestamp: number;
};

type ColorSegmentationRequestBody = {
  selection: SelectionAreaSelection;
  elements: [number, number][];
}

// Constants and injected values
const config = inject<FrontendConfig>("config")!;
const selection = computed(() => appState.selection.colorSegmentation);
const threshold = ref(20);
const number_clusters = ref(10);
const currentError = ref("Unknown error");
const colors = ref<string[]>([""]);
const selectedElement = ref<string>();
const useSelectionChecked = ref<boolean>(false);
const status = ref(Status.WAITING);

const elementsSelected = ref([{id: 1, name: selectedElement, threshold: threshold}])
const selectableElementsList = elements.value;

// Computed properties
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

  let selection: SelectionAreaSelection;

  if (useSelectionChecked.value) {
    selection = flipSelectionAreaSelection(currentAreaSelection.areaSelection, (await getTargetSize()).height);
  } else {
    selection = await getFullImageSelection();
  }

  let selectedElements: [number, number][];
  selectedElements = [];
  selectedElements.push([getElementIndex(selectedElement.value), threshold.value]);

  let request_body: ColorSegmentationRequestBody = {
    selection,
    elements: selectedElements
  };

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
    selection.value.element[0] = elementIndex;
    selection.value.enabled = Array(colors.value.length).fill(false);
    selection.value.colors = colors.value;
    selection.value.k = number_clusters.value;

    selection.value.threshold[0] = threshold.value;
    selection.value.useAreaSelection = useSelectionChecked.value;
    selection.value.areaSelection = deepClone(currentAreaSelection.areaSelection);
    selection.value.lastCompleteSelectionTimestamp = currentAreaSelection.lastChangedTimestamp;
  }

  const elementsSelectedRaw = elementsSelected.value;
  for (let i = 0; i < elementsSelectedRaw.length; i++) {
    if (elementsSelectedRaw[i] != undefined) {
      
    }
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
 * Adds a new element item with default values into the list of elements. Is used when the 
 * user presses the button "Add element"
 */
const addElementSelection = () => {
  const newElement = {
    id: elementsSelected.value.length + 1,
    name: selectedElement.value,
    threshold: threshold.value
  }
  elementsSelected.value.push(newElement);
}

/*
 * TODO: Write description.
 */
async function getFullImageSelection() {
  const size = await getTargetSize();
  const newAreaSelection: SelectionAreaSelection = {
    type: SelectionAreaType.Rectangle,
    points: [
      { x: 0, y: 0 },
      { x: size.width, y: size.height },
    ],
  };
  return newAreaSelection;
}

function removeElement(index: number) {
  // Only remove if there's more than 1 element in the list
  if (elementsSelected.value.length > 1) {
    elementsSelected.value.splice(index, 1);
  }
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
        <div class="flex align-bottom">
          <Checkbox id="recommendedClusterNumberCheck" title="Recommended number of clusters"/>
          <label for="recommendedClusterNumberCheck" class="text-sm ml-2">Recommended Number Clusters</label>
          <!--<Checkbox id="recommendedClusterNumberCheck" v-model:checked="" @update:checked="" />-->
        </div>
      </div>
      <!-- ELEMENTS SELECTION -->
      
      <div class="flex items-center space-x-4" v-for="(elementSel, index) in elementsSelected" :key = elementSel.id>
        <div class="grow space-y-1 max-w-36">
          <Label for="element">Element</Label>
          <Select v-model="elementSel.name" class="w-full">
            <SelectTrigger>
              <SelectValue placeholder="Select element" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="complete"> Complete painting </SelectItem>
              <SelectItem v-for="element in selectableElementsList" :key="element.name" :value="element.name">
                {{ element.name }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div class="flex-2 space-y-1">
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
      <Button variant="outline" @click="addElementSelection">Add element</Button>
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