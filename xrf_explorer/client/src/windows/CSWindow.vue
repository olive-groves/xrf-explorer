<script setup lang="ts">
import { ref, inject } from "vue";
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
const colors = ref([])
const selectedElement = ref();
const elements = ref([])


/**
 * Fetch the hexadecimal colors data.
 * @param url URL to the server API endpoint which provides the color hexadecimal numbers.
 * @returns True if the colors were fetched successfully, false otherwise.
 */
async function fetchColors(url: string) {
  // Make API call
  const response: Response = await fetch(`${url}/get_color_cluster`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });
  let fetchSuccessful: boolean = false;

  // Check that fetching was successful
  if (response.ok) {
    // Save the colors
    fetchSuccessful = await response
      .json()
      .then((data) => {
        colors.value = data;
        console.info("Successfully fetched colors", colors.value);
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
 * Fetch the names of the elements.
 * @param url URL to the server API endpoint which provides the elements names.
 * @returns True if the names were fetched successfully, false otherwise.
 */
 async function fetchElements(url: string) {
  // Make API call
  const response: Response = await fetch(`${url}/element_names`, {
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
    console.error("Error fetching average data", e);
  }

  try {
    // Whether the colors were fetched properly
    await fetchColors(config.api.endpoint);
  } catch (e) {
    console.error("Error fetching average data", e);
  }
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
    <div v-if="selectedElement" 
      v-for="color in colors" :key="color" class="color-shape" :style="{'background-color': color}">
      </div>
    </Window>
  </template>
