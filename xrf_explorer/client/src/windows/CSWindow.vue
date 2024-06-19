<script setup lang="ts">
import { ref, inject, computed, watch } from "vue";
import { appState, datasource, elements } from "@/lib/appState";
import { Window } from "@/components/ui/window";
import { ColorSegmentationSelection } from "@/lib/selection";
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

//Constants
const config = inject<FrontendConfig>("config")!;
const colors = ref<string>([]);
const selectedElement = ref<string>();
const selectedChannel = ref<boolean[]>();

const selection = computed(() => appState.selection.colorSegmentation);
const threshold = ref(40);
const number_clusters = ref(10);
const currentError = ref("Unknown error");

watch(datasource, () => {
  setup();
});

// Watch for changes in selectedElement and update colors accordingly
watch(selectedElement, (_) => {fetchColors});

// Status color segmentation
enum Status {
  WAITING,
  LOADING,
  ERROR,
  SUCCESS,
}
const status = ref(Status.WAITING);

/**
 * Fetch the hexadecimal colors data.
 * @param url URL to the server API endpoint which provides the color hexadecimal numbers.
 * @returns True if the colors were fetched successfully, false otherwise.
 */
async function fetchColors() {
  try {
    status.value = Status.LOADING;
    if (selectedElement.value == null) {
      currentError.value = "Please select an element";
      status.value = Status.ERROR;
      return;
    }
    const elementIndex = getElementIndex(selectedElement.value);
    const response = await fetch(`${config.api.endpoint}/${datasource.value}/cs/clusters/${elementIndex}/${number_clusters.value}/${threshold.value}`);
    if (!response.ok) throw new Error("Failed to fetch colors");
    console.log("Made it before");
    console.log(response);

    const data = await response.json();
    console.log("Made it after");
    console.log(data);
    colors.value = data;
    console.info("Successfully fetched colors", colors.value);
    status.value = Status.SUCCESS;
    return true;
  } catch (e) {
    toast.warning("Failed to retrieve colors");
    currentError.value = "Failed to generate color clusters";
    status.value = Status.ERROR;
    console.error(e);
    return false;
  }
}

/**
 * Initialize CS selection and window.
 */
async function setup() {
  // Initialize CS selection
  const sel: ColorSegmentationSelection = {
    element: 0,
    selected: false,
    enabled: Array(colors.length).fill(false),
    colors: [],
    k: number_clusters.value,
    elem_threshold: threshold.value,
  };
  selection.value = sel;

  selectedChannel.value = Array(colors.length).fill(false);
}

/**
 * Sets the CS selection.
 * @param selectedElement The selected element.
 * @param colorIndex The index of the selected color.
 */
function setSelection(selectedElement: string, colorIndex: number) {
  // Get index of selected element
  const index = getElementIndex(selectedElement);

  // Update selection
  selection.value.element = index;
  selection.value.enabled[colorIndex] = !selection.value[index].enabled[colorIndex];
}

/**
 * Returns the index of the given element.
 * @param elementName Name of element to get index of.
 * @returns Index of the element.
 */
function getElementIndex(elementName: string | undefined) {
  if (elementName == undefined) {
    return 0;
  }
  // Get index of new channel
  let index: number;
  if (elementName == "complete") {
    index = 0;
  } else {
    index = elements.value.findIndex((element) => element.name === elementName) + 1;
    if (index == 0) {
      console.error("Error fetching selected element");
      return 0;
    }
  }
  return index;
}
</script>

<template>
  <Window title="Color segmentaton" location="right">
    <div class="space-y-2 p-2">
      <!-- SELECTION MENU -->
      <!-- COLOR CLUSTER GENERATION -->
      <div class="flex space-x-2">
        <div class="grow space-y-1">
          <Label for="element">Element</Label>
          <Select v-model="selectedElement" class="w-full">
            <SelectTrigger>
              <SelectValue placeholder="Select an element" />
            </SelectTrigger>
            <SelectContent>
            <SelectItem value="complete"> Complete painting </SelectItem>
            <SelectItem v-for="element in elements" :key="element.channel" :value="element.name">
              {{ element.name }}
            </SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      <div class="flex space-x-2">
        <div class="w-28 shrink-0 space-y-1">
          <Label for="elemental_threshold">Threshold</Label>
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
        <div class="w-28 shrink-0 space-y-1">
          <Label for="number_clusters">Number of clusters</Label>
          <NumberField
            v-model="number_clusters"
            :min="0"
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
      <Button class="w-full" @click="fetchColors">Generate color clusters</Button>

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
            'ring-2 ring-foreground ring-offset-1 ring-offset-background':
              selection[getElementIndex(selectedElement)].enabled[colorIndex],
          }"
          @click="setSelection(selectedElement, colorIndex)"
        />
      </div>
    </div>
  </Window>
</template>
