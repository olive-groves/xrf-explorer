<script setup lang="ts">
import { ref, inject, computed, watch } from "vue";
import { appState, datasource } from "@/lib/appState";
import { Window } from "@/components/ui/window";
import { ColorSegmentationSelection } from "@/lib/selection"
import { FrontendConfig } from "@/lib/config";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

//Constants
const config = inject<FrontendConfig>("config")!;
const colors = ref<string[]>([]);
const colorsElements = ref<Record<string, string[]>>({});
const selectedElement = ref<string>();
const selectedChannel = ref<number>();
const elements = ref<string[]>([]);

const selection = computed(() => appState.selection.colorSegmentation);

watch(datasource,  () => {
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
    const response = await fetch(`${url}/${datasource.value}/get_color_cluster`);
    if (!response.ok) throw new Error("Failed to fetch colors");

    const data = await response.json();
    //assign the full color palette if the selection is made for the complete painting
    colorsElements.value["complete"] = data;
    //selection.value[0].numClusters = data.length;
    console.info("Successfully fetched colors", colorsElements.value["complete"]);
    return true;
  } catch (e) {
    console.error(e);
    return false;
  }
}


/**
 * Fetch the hexadecimal colors data per element.
 * @param url URL to the server API endpoint which provides the color hexadecimal numbers.
 * @returns True if the colors were fetched successfully, false otherwise.
 */
 async function fetchElementColors(url: string) {
  try {
    const response = await fetch(`${url}/${datasource.value}/get_element_color_cluster`);
    if (!response.ok) throw new Error("Failed to fetch element colors");

    const data = await response.json();
    //for each element assign the corresponding palette at that index
    elements.value.forEach((element, index) => {
      colorsElements.value[element] = data[index];
      //selection.value[index].numClusters = data[index].length;
    });
    console.info("Successfully fetched element colors", colorsElements.value);
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
      color: "#FFFFFF",
    };
    selection.value.push(sel);
  }

  try {
    // Whether the colors were fetched properly
    await fetchColors(config.api.endpoint);
  } catch (e) {
    console.error("Error fetching colors data", e);
  }
  try {
    // Whether the colors were fetched properly
    await fetchElementColors(config.api.endpoint);
  } catch (e) {
    console.error("Error fetching element colors data", e);
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
  selection.value.forEach(channel => {
    channel.selected = false;
  });

  // Get index of new channel
  let index: number;
  if (selectedElement == "complete") {
    index = 0;
  } else {
    index = elements.value.findIndex(element => element === selectedElement) + 1;
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


<style scoped>
/**
 * Shape of clusters in color palette
 */
.color-shape {
  width: 70px; 
  height: 100px; /* Adjust height*/
  border-radius: 10%; /* Makes rounded edges */
  margin: 5px; /* Adds space between the shapes */
  display: inline-block; /* Allows shapes to line up horizontally */
}

.color-shape.selected {
  border: 2px solid #FFFFFF;
}

</style>

<template>
  <Window title="Color Segmentation Window" opened location="right">
    <!-- SELECTION MENU -->
    <div class="mt-1 flex items-center">
      <Select v-model="selectedElement">
        <SelectTrigger class="ml-1 mb-2 w-40">
          <SelectValue placeholder="Select an element" />
        </SelectTrigger>
        <SelectContent>
          <SelectGroup>
            <SelectLabel>Elements</SelectLabel>
            <SelectItem value="complete"> Complete painting </SelectItem>
            <SelectItem v-for="element in elements" :key="element" :value="element"> {{ element }}  </SelectItem>
          </SelectGroup>
        </SelectContent>
      </Select>
    </div>

    <!-- COLOR PALETTE --> 
    <div v-if="selectedElement" class="color-palette">
      <div 
        v-for="(color, colorIndex) in colors" 
        :key="color" 
        class="color-shape" 
        :style="{'background-color': color}"
        :class="{'selected': selectedChannel === colorIndex}"
        @click="setSelection(selectedElement, color, colorIndex)"
      ></div>
    </div>
    </Window>
  </template>
