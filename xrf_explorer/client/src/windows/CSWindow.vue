<script setup lang="ts">
import { computed, ComputedRef, inject, ref, watch } from "vue";
import { appState, datasource, elementalDataPresent, elements } from "@/lib/appState";
import { Window } from "@/components/ui/window";
import { LoaderPinwheel, Trash2} from "lucide-vue-next";
import { FrontendConfig } from "@/lib/config";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "vue-sonner";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
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
import { getTooltipByKey } from "@/lib/useToolTips";

enum Status {
  WAITING,
  LOADING,
  ERROR,
  SUCCESS,
}

const recommendedStatus = ref(Status.WAITING);

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
const number_clusters = ref(10);
const currentError = ref("Unknown error");
const colors = ref<string[]>([""]);
const useSelectionChecked = ref<boolean>(false);
const status = ref(Status.WAITING);

const elementsSelected = ref([{id: 1, name: "", threshold: 20}])
const selectableElementsList = computed(() => elements.value);
const disabledElements = computed(() => {
  // Collect all currently selected names (except empty and 'complete')
  return elementsSelected.value
    .map(e => e.name)
    .filter(name => name && name !== 'complete');
});

// Dialog visibility ref for confirmation
const showConfirmDialog = ref(false);
let pendingElementsSelected: typeof elementsSelected.value | null = null;

function handleConfirm(choice: boolean) {
  if (choice) {
    elementsSelected.value = [{ id: 1, name: 'complete', threshold: elementsSelected.value[0].threshold }];
  } else {
    if (pendingElementsSelected) {
      const firstNonComplete = pendingElementsSelected.find(sel => sel.name && sel.name !== 'complete');
      if (firstNonComplete) {
        elementsSelected.value = [firstNonComplete];
      } else {
        elementsSelected.value = pendingElementsSelected.map(e =>
          e.name === 'complete' ? { ...e, name: '' } : e
        );
      }
    }
  }
  pendingElementsSelected = null;
  showConfirmDialog.value = false;
}

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

// Watch for selection of "complete" with other elements, and confirm with user
watch(
  elementsSelected,
  (newVal) => {
    const hasComplete = newVal.some(sel => sel.name === 'complete');
    const hasOtherElements = newVal.some(sel => sel.name && sel.name !== '' && sel.name !== 'complete');

    if (hasComplete && hasOtherElements) {
      // Open dialog instead of window.confirm
      pendingElementsSelected = [...newVal];
      showConfirmDialog.value = true;
    }
  },
  { deep: true }
);

/**
 * Fetch the hexadecimal colors' data.
 * @returns True if the colors were fetched successfully, false otherwise.
 */
async function fetchColors() {
  status.value = Status.LOADING;
  if (elementsSelected.value[0] == null) {
    currentError.value = "Please select an element";
    status.value = Status.ERROR;
    return;
  }

  //Read the selection for the payload
  let activeSelection: SelectionAreaSelection;
  if (useSelectionChecked.value) {
    activeSelection = flipSelectionAreaSelection(currentAreaSelection.areaSelection, (await getTargetSize()).height);
  } else {
    activeSelection = await getFullImageSelection();
  }

  //Read the elements for the payload
  let selectedElements: [number, number][];
  selectedElements = [];
  for(let i = 0; i < elementsSelected.value.length; i++) {
    selectedElements.push([getElementIndex(elementsSelected.value[i].name), elementsSelected.value[i].threshold]);
  }

  //Create payload json
  let request_body: ColorSegmentationRequestBody = {
    selection: activeSelection,
    elements: selectedElements
  };

  //Perform request
  const response = await fetch(
    `${config.api.endpoint}/${datasource.value}/cs/clusters/` +
      `/${number_clusters.value}/${useSelectionChecked.value}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request_body),
    },
  );
  selection.value.lastColorSegmentationRun = Date.now();

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
  if (selection.value != undefined) {
    // Update selection
    selection.value.elements = [] as number[];
    selection.value.thresholds = [] as number[];
    for (var i = 0; i < elementsSelected.value.length; i++) {
      selection.value.elements.push(getElementIndex(elementsSelected.value[i].name));
      selection.value.thresholds.push(elementsSelected.value[i].threshold);
    }

    selection.value.enabled = Array(colors.value.length).fill(false);
    selection.value.colors = colors.value;
    selection.value.k = number_clusters.value;

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
 * Enables all color clusters
 */
function enableAllClusters() {
  for (var i = 0; i < selection.value.enabled.length; i++) {
    if (selection.value.enabled[i] != undefined) {
      selection.value.enabled[i] = true;
    }
  }
}

/**
 * Disables all color clusters
 */
function disableAllClusters() {
  for (var i = 0; i < selection.value.enabled.length; i++) {
    if (selection.value.enabled[i] != undefined) {
      selection.value.enabled[i] = false;
    }
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
    name: "",
    threshold: 20
  }
  elementsSelected.value.push(newElement);
}

/**
 * Remove an element from the selected elements list.
 * @param index the index of the element in the list to be removed.
 */
function removeElement(index: number) {
  // Only remove if there's more than 1 element in the list
  if (elementsSelected.value.length > 1) {
    elementsSelected.value.splice(index, 1);
  }
}

/*
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

const recommendedClusters = ref<number | null>(null);

// Calculate recommended clusters
async function calculateRecommendedClusters() {
  try {
    // Catch when the user hasn't selected an element.
    for (const sel of elementsSelected.value) {
      if (!sel || !sel.name || sel.threshold === undefined) {
        toast.error("Invalid element selection");
        return;
      }
    }

    recommendedStatus.value = Status.LOADING;
    // Prepare request
    const response = await fetch(
      `${config.api.endpoint}/${datasource.value}/cs/recommend-k`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          selection: flipSelectionAreaSelection(
            currentAreaSelection.areaSelection,
            (await getTargetSize()).height
          ),
          elements: elementsSelected.value.map((sel) => [
            getElementIndex(sel.name),
            sel.threshold,
          ]),
        }),
      }
    );
    // Handle response
    if (!response.ok) {
      recommendedStatus.value = Status.ERROR;
      toast.error("Failed to calculate recommended clusters");
      return;
    }
    // Get data
    const data = await response.json();
    recommendedClusters.value = data.recommended_k;
    recommendedStatus.value = Status.SUCCESS;
  } catch (err) {
    recommendedStatus.value = Status.ERROR;
    console.error(err);
    toast.error("Error calculating recommended clusters");
  }
}

// Update number of clusters variable to match the calculated recommended number of clusters.
async function setRecommendedClusters() {
  if (recommendedClusters.value == null) {
    return;
  }
  number_clusters.value = recommendedClusters.value;
} 

</script>

<template>
  <Window
    title="Color segmentation"
    :help="getTooltipByKey('Toolbar.color_segmentation')"
    location="right"
    :disabled="!elementalDataPresent"
  >
    <div class="space-y-2 p-2">
      <!-- USE SELECTION AREA CHECKBOX -->
      <div class="flex items-center space-x-2">
        <Checkbox id="use_selection_area" class="align-bottom" v-model:checked="useSelectionChecked" />
        <Label for="use_selection_area" class="align-middle">Use only selection area</Label>
      </div>
      <div class="border-t border-border flex flex-col space-y-1.5 pt-2">
        <Label for="recommendClusters">Recommended Amount of Clusters:</Label>
        <div class="flex flex-nowrap space-x-2 w-full">
          <div class="basis-2/5 min-w-0 p-1">
            <Button class="w-full h-full text-center whitespace-normal" @click="calculateRecommendedClusters">
              Calculate
            </Button>
          </div>
          <div class="basis-3/5 min-w-0 p-1">
            <Button
              class="w-full h-full text-center whitespace-normal"
              :disabled="recommendedStatus !== Status.SUCCESS"
              @click="setRecommendedClusters"
            >
              <template v-if="recommendedStatus === Status.LOADING">
                Loading...
              </template>

              <template v-else>
                Use recommended ({{ recommendedClusters || '' }})
              </template>
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
      <!-- ELEMENT SELECTION -->
      <div class="flex items-center space-x-4" v-for="(elementSel, index) in elementsSelected" :key = elementSel.id>
        <div class="grow space-y-1 max-w-36">
          <Label for="element">Element</Label>
          <Select v-model="elementSel.name" class="w-full">
            <SelectTrigger>
              <SelectValue placeholder="Select element" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem
                value="complete"
                :disabled="elementsSelected.some(sel => sel.name === 'complete')"
              >
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
      <Button
        variant="outline"
        @click="addElementSelection"
        :disabled="elementsSelected.length >= selectableElementsList.length || elementsSelected.some(sel => sel.name === 'complete')"
      >
        Add element
      </Button>
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
            'ring-2 ring-foreground ring-offset-1 ring-offset-background': selection.enabled[colorIndex],
          }"
          @click="toggleCluster(colorIndex)"
        />
      </div>
      <div v-if="status == Status.SUCCESS && colors.length > 0" class="flex gap-2 w-full">
        <Button class="basis-1/2" variant="outline" @click="enableAllClusters">Select All</Button>
        <Button class="basis-1/2" variant="outline" @click="disableAllClusters">Deselect All</Button>
      </div>
    </div>
    <Dialog v-model:open="showConfirmDialog">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Confirm Selection</DialogTitle>
          <DialogDescription>
            <div class="mt-3">
            Selecting 'Complete painting' will remove all other selected elements. Continue?
            </div>
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
