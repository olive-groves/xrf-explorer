<script setup lang="ts">
import { ref, inject, computed, watch } from "vue";
import { appState, datasource, elements } from "@/lib/appState";
import { Window } from "@/components/ui/window";
import { ColorSegmentationSelection } from "@/lib/selection";
import { LoaderPinwheel } from "lucide-vue-next";
import { FrontendConfig } from "@/lib/config";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "vue-sonner";

//Constants
const config = inject<FrontendConfig>("config")!;
const colors = ref<string[]>([]);
const colorsElements = ref<Record<string, string[]>>({});
const selectedElement = ref<string>();
const selectedChannel = ref<boolean[]>();

const selection = computed(() => appState.selection.colorSegmentation);

watch(datasource, () => {
  setup();
});

watch(colorsElements, () => {
  if (selectedElement.value) {
    if (selectedElement.value === "complete") {
      colors.value = colorsElements.value["complete"];
    } else {
      colors.value = colorsElements.value[selectedElement.value] || [];
    }
  }
});

// Watch for changes in selectedElement and update colors accordingly
watch(selectedElement, (newValue) => {
  selection.value.forEach((channel) => {
    channel.selected = false;
  });
  if (newValue === "complete") {
    colors.value = colorsElements.value["complete"];
  } else if (newValue) {
    colors.value = colorsElements.value[newValue] || [];
  }
  selection.value[getElementIndex(newValue)].selected = true;
});

// Status color segmentation
enum Status {
  LOADING,
  ERROR,
  SUCCESS,
}
const status = ref(Status.LOADING);

/**
 * Fetch the hexadecimal colors data.
 * @param url URL to the server API endpoint which provides the color hexadecimal numbers.
 * @returns True if the colors were fetched successfully, false otherwise.
 */
async function fetchColors(url: string) {
  try {
    const response = await fetch(`${url}/${datasource.value}/cs/clusters`);
    if (!response.ok) throw new Error("Failed to fetch colors");

    const data = await response.json();
    //assign the full color palette if the selection is made for the complete painting
    colorsElements.value["complete"] = data[0];
    elements.value.forEach((element, index) => {
      colorsElements.value[element.name] = data[index + 1];
    });
    console.info("Successfully fetched colors", colorsElements.value["complete"]);
    return true;
  } catch (e) {
    toast.warning("Failed to retrieve colors");
    console.error(e);
    return false;
  }
}

/**
 * Show the colors and element names, and initialize CS selection.
 */
async function setup() {
  try {
    // Whether the colors were fetched properly
    await fetchColors(config.api.endpoint);
  } catch (e) {
    status.value = Status.ERROR;
    toast.warning("Failed to retrieve painting colors");
    console.error("Error fetching colors data", e);
  }
  status.value = Status.SUCCESS;

  // Initialize CS selection
  const colors = colorsElements.value["complete"];
  const sel: ColorSegmentationSelection = {
    element: 0,
    selected: false,
    enabled: Array(colors.length).fill(false),
    colors: colors,
  };
  selection.value.push(sel);

  selectedChannel.value = Array(colors.length).fill(false);

  for (let i = 1; i <= elements.value.length; i++) {
    const colors = colorsElements.value[elements.value[i - 1].name];
    const sel: ColorSegmentationSelection = {
      element: i,
      selected: false,
      enabled: Array(colors.length).fill(false),
      colors: colors,
    };
    selection.value.push(sel);
  }
}

/**
 * Sets the CS selection.
 * @param selectedElement The selected element.
 * @param colorIndex The index of the selected color.
 */
function setSelection(selectedElement: string, colorIndex: number) {
  // Deselect all channels
  selection.value.forEach((channel) => {
    channel.selected = false;
  });

  // Get index of selected element
  const index = getElementIndex(selectedElement);

  // Update selection
  selection.value[index].selected = true;
  selection.value[index].enabled[colorIndex] = !selection.value[index].enabled[colorIndex];
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
      <div class="flex items-center" v-if="status == Status.SUCCESS">
        <Select v-model="selectedElement">
          <SelectTrigger class="w-40">
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

      <!-- LOADING/ERROR MESSAGES -->
      <div
        class="flex flex-col items-center justify-center space-y-2 p-8"
        v-if="status == Status.LOADING || status == Status.ERROR"
      >
        <span v-if="status == Status.LOADING">Loading...</span>
        <div v-if="status == Status.LOADING" class="size-6">
          <LoaderPinwheel class="size-full animate-spin" />
        </div>
        <span v-if="status == Status.ERROR"> An error ocurred while loading the color clusters. </span>
      </div>

      <!-- COLOR PALETTE -->
      <div v-if="selectedElement && status == Status.SUCCESS" class="flex flex-wrap gap-2">
        <div
          v-for="(color, colorIndex) in colors"
          :key="color"
          :style="{ 'background-color': color }"
          class="inline-block size-12 rounded-md"
          :class="{
            'ring ring-foreground': selection[getElementIndex(selectedElement)].enabled[colorIndex],
          }"
          @click="setSelection(selectedElement, colorIndex)"
        />
      </div>
    </div>
  </Window>
</template>
