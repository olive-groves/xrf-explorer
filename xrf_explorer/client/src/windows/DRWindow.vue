<script setup lang="ts">
import {onMounted, ref} from "vue";

import { inject } from "vue";
import { useFetch } from "@vueuse/core";
import { FrontendConfig } from "@/lib/config";

import * as d3 from "d3";

// Constants
const config = inject<FrontendConfig>("config")!;
const URL_IMAGE = `${config.api.endpoint}/get_dr_overlay`;
const URL_EMBEDDING = `${config.api.endpoint}/get_dr_embedding`;

// Status dimensionality reduction
enum Status {
  LOADING,
  GENERATING,
  ERROR,
  SUCCESS,
  WELCOME,
}
const status = ref(Status.WELCOME);
const currentError = ref("Unknown error.");

// Dimensionality reduction parameters
const threshold = ref([100]);
const selectedElement = ref();
const selectedOverlay = ref();

// Dimensionality reduction image
const imageSourceUrl = ref();

// Selection
const drImage = ref(null);
const selectedPoints: { x: number; y: number }[] = [];
const mrIncredible: string = "src/windows/mr-incredible.png";

// canvas to draw on
const canvas = ref<HTMLCanvasElement>(<HTMLCanvasElement>document.getElementById("canvas"));
const context = ref<CanvasRenderingContext2D | null>(canvas.value?.getContext("2d"));

function setup() {
  const svg = d3.select(drImage.value)
      .append("svg")
      .attr("width", 640)
      .attr("height", 640);

  // const mr_incredible = svg
  //     .append("img")
  //     .attr("xlink:href", "file:///C:/Users/20210682/Documents/sep/xrf-explorer/xrf_explorer/client/src/windows/mr-incredible.png")
  //     // .attr("xlink:href", "https://www.google.com/url?sa=i&url=https%3A%2F%2Fwww.reddit.com%2Fr%2FMemeTemplatesOfficial%2Fcomments%2Frt9bc8%2Fmr_incredible_becomes_ascended%2F&psig=AOvVaw2tzjoDgI25vxwQ-M_sHdAk&ust=1717242705408000&source=images&cd=vfe&opi=89978449&ved=0CBIQjRxqFwoTCJiRmt3pt4YDFQAAAAAdAAAAABAE")
  //     .attr("width", 640)
  //     .attr("height", 640);

  svg.append("rect")
      .attr("x", 100)
      .attr("y", 100)
      .attr("width", 200)
      .attr("height", 200)
      .attr("fill", "red")
      .attr("opacity", 1);
}

/**
 * Fetch the dimensionality reduction image
 * Sets status to corresponding value
 * For the rest it uses the fetchBlob function.
 */
async function fetchDRImage() {
  // Check if the user specified an overlay
  if (selectedOverlay.value == null) {
    currentError.value = "Please select an overlay.";
    status.value = Status.ERROR;
    return;
  }

  status.value = Status.LOADING;

  // Set the overlay type
  const url = new URL(URL_IMAGE);
  url.searchParams.set("type", selectedOverlay.value.toString());

  // Fetch the image
  const { response, data } = await useFetch(url.toString()).get().blob();

  // Check if fetching the image was successful
  if (response.value?.ok && data.value != null) {
    // Create URL for image and set it globally
    imageSourceUrl.value = URL.createObjectURL(data.value).toString();

    // Update status
    status.value = Status.SUCCESS;
  } else {
    currentError.value = "Loading overlay failed.";
    status.value = Status.ERROR;
  }
}

/**
 * Compute the embedding
 * Sets status to corresponding value
 * If embedding was generated successfully, it fetches the new image.
 */
async function updateEmbedding() {
  // Check if an element and overlay were selected, if not return message to user.
  if (selectedOverlay.value == null) {
    currentError.value = "Please select an overlay.";
    status.value = Status.ERROR;
    return;
  } else if (selectedElement.value == null) {
    currentError.value = "Please select an element.";
    status.value = Status.ERROR;
    return;
  }

  status.value = Status.GENERATING;

  // Create URL for embedding
  const _url = new URL(URL_EMBEDDING);
  _url.searchParams.set("element", selectedElement.value.toString());
  _url.searchParams.set("threshold", threshold.value.toString());

  // Create the embedding
  const { response, data } = await useFetch(_url.toString()).get().blob();

  // Check if fetching the image was successful
  if (response.value?.ok && data.value != null) {
    // Load the new embedding
    await fetchDRImage();
    return;
  }

  // Set status to error
  currentError.value = "Generating embedding failed.";
  status.value = Status.ERROR;
}

function onMouseDown(event: MouseEvent) {
  selectedPoints.push({x: event.clientX, y: event.clientY});
  visualizeSelectedPoints();
}

function visualizeSelectedPoints() {
  for (const point of selectedPoints) {
    console.log("visualizing point at: ", point.x, point.y, context);
    if (context) {
      context.value?.fillRect(point.x, point.y, 10, 10);
      console.log("placed point at: ", point.x, point.y);
    }
  }
}
</script>

<template>
  <Window title="Dimensionality reduction" opened @window-mounted="setup">
    <!-- OVERLAY SECTION -->
    <div class="p-2">
      <p class="font-bold">Overlay:</p>
      <div class="mt-1 flex items-center">
        <Select v-model="selectedOverlay">
          <SelectTrigger class="w-32">
            <SelectValue placeholder="Select an overlay" />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectLabel>Overlays</SelectLabel>
              <SelectItem value="rgb"> RGB </SelectItem>
              <SelectItem value="uv"> UV </SelectItem>
              <SelectItem value="xray"> XRay </SelectItem>
              <SelectItem value="0"> Element 0 </SelectItem>
              <SelectItem value="1"> Element 1 </SelectItem>
              <SelectItem value="9"> Element 9 </SelectItem>
            </SelectGroup>
          </SelectContent>
        </Select>
        <Button class="ml-4 block w-28" @click="fetchDRImage">Show overlay</Button>
      </div>
      <!-- PARAMETERS SECTIONS -->
      <Separator class="my-2" />
      <p class="font-bold">Parameters:</p>
      <Slider class="mt-2 w-64" v-model="threshold" id="threshold" :min="0" :max="255" :step="1" />
      <div class="-mt-1">
        <span class="text-xs italic">Threshold value: </span>
        <span class="text-xs italic">{{ threshold?.[0] }}</span>
      </div>
      <div class="mt-1 flex items-center">
        <Select v-model="selectedElement">
          <SelectTrigger class="w-32">
            <SelectValue placeholder="Select an element" />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectLabel>Elements</SelectLabel>
              <SelectItem value="0"> Element 0 </SelectItem>
              <SelectItem value="1"> Element 1 </SelectItem>
              <SelectItem value="9"> Element 9 </SelectItem>
            </SelectGroup>
          </SelectContent>
        </Select>
        <Button class="ml-4 block w-28" @click="updateEmbedding">Generate</Button>
      </div>
      <!-- GENERATION OF THE IMAGE -->
      <Separator class="my-2" />
      <p class="font-bold">Generated image:</p>
<!--      <div class="mt-1 flex aspect-square items-center justify-center text-center" style="cursor: crosshair" @mousedown="onMouseDown">-->
<!--        <span v-if="status == Status.WELCOME">Choose your overlay and parameters and start the generation.</span>-->
<!--        <span v-if="status == Status.LOADING">Loading...</span>-->
<!--        <span v-if="status == Status.GENERATING">Generating...</span>-->
<!--        <span v-if="status == Status.ERROR">{{ currentError }}</span>-->
<!--        <img v-if="status == Status.SUCCESS" :src="imageSourceUrl" @error="status = Status.ERROR" />-->
<!--      </div>-->
      <div class="mt-1 flex aspect-square items-center justify-center text-center" style="cursor: crosshair; position: relative" @mousedown="onMouseDown" id="svg-container">
<!--        <span v-if="status == Status.WELCOME">Choose your overlay and parameters and start the generation.</span>-->
<!--        <span v-if="status == Status.LOADING">Loading...</span>-->
<!--        <span v-if="status == Status.GENERATING">Generating...</span>-->
<!--        <span v-if="status == Status.ERROR">{{ currentError }}</span>-->
<!--        <svg v-if="status == Status.SUCCESS" ref="drImage"></svg>-->
        <img :src="mrIncredible" @error="status = Status.ERROR" />
        <svg ref="drImage" style="position: absolute"></svg>
      </div>
    </div>
  </Window>
</template>
