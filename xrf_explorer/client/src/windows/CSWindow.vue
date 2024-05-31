<script setup lang="ts">
import { ref, inject, watch } from "vue";
import { appState, datasource } from "@/lib/appState";
import { Window } from "@/components/ui/window";
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
const elements = ref<string[]>([]);


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
 * Show the colors and element names.
 */
async function showColors() {
  try {
    // Whether the colors were fetched properly
    await fetchElements(config.api.endpoint);
  } catch (e) {
    console.error("Error fetching names data", e);
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

// Watch for changes in selectedElement and update colors accordingly
watch(selectedElement, (newValue) => {
  if (newValue === "complete") {
    colors.value = colorsElements.value["complete"];
  } else if (newValue) {
    colors.value = colorsElements.value[newValue] || [];
  } 
});

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
</style>

<template>
  <Window title="Color Segmentation Window" @window-mounted="showColors" opened location="right">
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
      <div v-for="color in colors" :key="color" class="color-shape" :style="{'background-color': color}"></div>
      </div>
    </Window>
  </template>
