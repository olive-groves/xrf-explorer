<script setup lang="ts">
import { ref, inject, computed, watch } from "vue";
import { appState, datasource } from "@/lib/appState";
import { Window } from "@/components/ui/window";
import { ColorSegmentationSelection } from "@/lib/selection";
import { FrontendConfig } from "@/lib/config";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

//Constants
const config = inject<FrontendConfig>("config")!;
const colors = ref<string[]>([]);
const colorsElements = ref<Record<string, string[]>>({});
const selectedElement = ref<string>();
const selectedChannel = ref<number>();
const elements = ref<string[]>([]);

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
    selectedChannel.value = -1;
  } else if (newValue) {
    colors.value = colorsElements.value[newValue] || [];
    selectedChannel.value = -1;
  }
});

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
      colorsElements.value[element] = data[index + 1];
    });
    console.info("Successfully fetched colors", colorsElements.value["complete"]);
    return true;
  } catch (e) {
    console.error(e);
    return false;
  }
}

/**
 * Fetch the names of the elements.
 * @param url URL to the server API endpoint which provides the elements names.
 * @returns True if the names were fetched successfully, false otherwise.
 */
async function fetchElements(url: string) {
  // Make API call
  const response: Response = await fetch(`${url}/${appState.workspace?.name}/element_names`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });
  let fetchSuccessful: boolean = false;

  // Check that fetching the names was successful
  if (response.ok) {
    // Save the names
    fetchSuccessful = await response
      .json()
      .then((data) => {
        elements.value = data;
        console.info("Successfully fetched names", elements.value);
        return true;
      })
      .catch((e) => {
        console.error(e);
        return false;
      });
  } else {
    // Error response
    fetchSuccessful = await response
      .text()
      .then((data) => {
        console.info(data);
        return false;
      })
      .catch((e) => {
        console.error(e);
        return false;
      });
  }

  return fetchSuccessful;
}

/**
 * Show the colors and element names, and initialize CS selection.
 */
async function setup() {
  try {
    // Whether the colors were fetched properly
    await fetchElements(config.api.endpoint);
  } catch (e) {
    console.error("Error fetching names data", e);
  }

  // Initialize CS selection
  for (let i = 0; i <= elements.value.length; i++) {
    const sel: ColorSegmentationSelection = {
      element: i,
      channel: 1,
      selected: false,
      prevChannel: 1,
      color: "#ffffff",
    };
    selection.value.push(sel);
  }

  try {
    // Whether the colors were fetched properly
    await fetchColors(config.api.endpoint);
  } catch (e) {
    console.error("Error fetching colors data", e);
  }
}

/**
 * Sets the CS selection.
 * @param selectedElement The selected element.
 * @param color The selected color.
 * @param colorIndex The index of the selected color.
 */
function setSelection(selectedElement: string, color: string, colorIndex: number) {
  // Deselect all channels
  selection.value.forEach((channel) => {
    channel.selected = false;
  });

  // Get index of new channel
  let index: number;
  if (selectedElement == "complete") {
    index = 0;
  } else {
    index = elements.value.findIndex((element) => element === selectedElement) + 1;
    if (index == 0) {
      console.error("Error fetching selected element");
      return;
    }
  }
  selectedChannel.value = colorIndex;

  // Update selection
  selection.value[index].prevChannel = selection.value[index].channel;
  selection.value[index].channel = colorIndex + 1;
  selection.value[index].color = color;
  selection.value[index].selected = true;
}
</script>

<template>
  <Window title="Color segmentaton" location="right">
    <!-- SELECTION MENU -->
    <div class="mt-1 flex items-center">
      <Select v-model="selectedElement">
        <SelectTrigger class="mb-2 ml-1 w-40">
          <SelectValue placeholder="Select an element" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="complete"> Complete painting </SelectItem>
          <SelectItem v-for="element in elements" :key="element" :value="element"> {{ element }} </SelectItem>
        </SelectContent>
      </Select>
    </div>

    <!-- COLOR PALETTE -->
    <div v-if="selectedElement" class="flex flex-wrap">
      <div
        v-for="(color, colorIndex) in colors"
        :key="color"
        :style="{ 'background-color': color }"
        class="m-1 inline-block h-24 w-16 rounded-md"
        :class="{ 'border-2 border-border': selectedChannel === colorIndex }"
        @click="setSelection(selectedElement, color, colorIndex)"
      ></div>
    </div>
  </Window>
</template>
