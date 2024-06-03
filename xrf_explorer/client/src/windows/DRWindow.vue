<script setup lang="ts">
import {ref, computed} from "vue";
import {appState, datasource, elements} from "@/lib/appState";
import {inject} from "vue";
import {useFetch} from "@vueuse/core";
import {FrontendConfig} from "@/lib/config";
import {ContextualImage} from "@/lib/workspace";
import {LoaderPinwheel} from "lucide-vue-next";
import {LabeledSlider} from "@/components/ui/slider";
import {toast} from "vue-sonner";
import {SelectionTool, SelectionOption} from "@/components/functional/selection/selection_tool.ts";

import * as d3 from "d3";

// Constants
const config = inject<FrontendConfig>("config")!;
const contextualImages = computed(() => {
  const allImages: ContextualImage[] = [];

  // Get all contextual images
  const baseImage = appState.workspace?.baseImage;
  const contextualImages = appState.workspace?.contextualImages ?? [];

  // Add the base image and the contextual images to the list of all images
  if (baseImage != undefined) {
    allImages.push(baseImage);
  }
  if (contextualImages != undefined) {
    allImages.push(...contextualImages);
  }

  return allImages;
});

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
const svgOverlay = ref(null);
const selectionTool = new SelectionTool();
const mrIncredible: string = "src/windows/mr-incredible.png";

function drawSelection() {

  // Remove old selection
  const svg = d3.select(svgOverlay.value);
  svg.selectAll("*").remove();

  // Get the image so we can extract the dimensions
  const image = document.getElementById("image");
  if (image == null) return;

  console.log("dimensions: ", image.getBoundingClientRect().width, image.getBoundingClientRect().height);

  svg.attr("x", image.getBoundingClientRect().left)
      .attr("y", image.getBoundingClientRect().top)
      .attr("width", image.getBoundingClientRect().width)
      .attr("height", image.getBoundingClientRect().height);

  if (selectionTool.selectionType == SelectionOption.Rectangle) {
    console.log("Drawing rectangle from: ", selectionTool.getOrigin().x, selectionTool.getOrigin().y, " to: ", selectionTool.getOrigin().x + selectionTool.getWidth(), selectionTool.getOrigin().y + selectionTool.getHeight());
    svg.append("rect")
        .attr("x", selectionTool.getOrigin().x)
        .attr("y", selectionTool.getOrigin().y)
        .attr("width", selectionTool.getWidth())
        .attr("height", selectionTool.getHeight())
        .attr("fill", config.selectionToolConfig.color)
        .attr("opacity", config.selectionToolConfig.opacity);
  }
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
  const apiURL = `${config.api.endpoint}/${datasource.value}/dr/overlay/${selectedOverlay.value}`;

  // Fetch the image
  const {response, data} = await useFetch(apiURL).get().blob();

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
  const apiURL = `${config.api.endpoint}/${datasource.value}/dr/embedding/${selectedElement.value}/${threshold.value}`;

  // Create the embedding
  const {response, data} = await useFetch(apiURL).get().text();

  // Check if fetching the image was successful
  if (response.value?.ok && data.value != null) {
    if (data.value == "downsampled") {
      toast.warning("Downsampled data points", {
        description:
            "The total number of data points for the embedding has been downsampled to prevent excessive waiting times.",
      });
    }

    // Load the new embedding
    await fetchDRImage();
    return;
  }

  // Set status to error
  currentError.value = "Generating embedding failed.";
  status.value = Status.ERROR;
}

function onMouseDown(event: MouseEvent) {

  if (event.button == config.selectionToolConfig.cancelButton)
    selectionTool.cancelSelection();

  else if (event.button == config.selectionToolConfig.addPointButton) {

    const svg: HTMLElement | null = document.getElementById("svgOverlay");
    if (svg != null) {
      const clickedPos = {
        x: event.clientX - svg.getBoundingClientRect().left,
        y: event.clientY - svg.getBoundingClientRect().top
      };
      selectionTool.addPointToSelection(clickedPos);
    }
  }

  visualizeSelection();
}

function visualizeSelection() {
  if (selectionTool.finishedSelection)
    drawSelection();
}
</script>

<template>
  <Window title="Dimensionality reduction" location="left" @window-mounted="visualizeSelection">
    <!-- OVERLAY SECTION -->
    <div class="p-2">
      <p class="font-bold">Overlay:</p>
      <div class="mt-1 flex items-center">
        <Select v-model="selectedOverlay">
          <SelectTrigger>
            <SelectValue placeholder="Select an overlay"/>
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectLabel>Contextual images:</SelectLabel>
              <SelectItem v-for="image in contextualImages" :key="image.name" :value="'contextual_' + image.name">
                {{ image.name }}
              </SelectItem>
            </SelectGroup>
            <SelectGroup>
              <SelectLabel>Elements:</SelectLabel>
              <SelectItem v-for="element in elements" :key="element.channel" :value="'elemental_' + element.channel">
                {{ element.name }}
              </SelectItem>
            </SelectGroup>
          </SelectContent>
        </Select>
        <Button class="ml-2 w-40" @click="fetchDRImage">Show overlay</Button>
      </div>
      <!-- PARAMETERS SECTIONS -->
      <p class="mt-4 font-bold">Embedding:</p>
      <LabeledSlider label="Threshold" v-model="threshold" :min="0" :max="255" :step="1" :default="[100]"/>
      <div class="mt-1 flex items-center">
        <Select v-model="selectedElement">
          <SelectTrigger>
            <SelectValue placeholder="Select an element"/>
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectLabel>Elements</SelectLabel>
              <SelectItem v-for="element in elements" :key="element.channel" :value="element.channel">
                {{ element.name }}
              </SelectItem>
            </SelectGroup>
          </SelectContent>
        </Select>
        <Button class="ml-2 w-40" @click="updateEmbedding">Generate</Button>
      </div>
      <!-- GENERATION OF THE IMAGE -->
      <p class="mt-4 font-bold">Generated image:</p>
      <div
          class="mt-1 flex aspect-square flex-col items-center justify-center space-y-2 text-center pointer-events-auto"
          style="cursor: crosshair; position: relative" @mousedown="onMouseDown" id="imageContainer">
        <!--        <span v-if="status == Status.WELCOME">Choose your overlay and paramaters and start the generation.</span>-->
        <!--        <span v-if="status == Status.LOADING">Loading</span>-->
        <!--        <span v-if="status == Status.GENERATING">Generating</span>-->
        <!--        <span v-if="status == Status.ERROR">{{ currentError }}</span>-->
        <!--        <div v-if="status == Status.LOADING || status == Status.GENERATING" class="size-6">-->
        <!--          <LoaderPinwheel class="size-full animate-spin" />-->
        <!--        </div>-->
        <!--        <img v-if="status == Status.SUCCESS" :src="imageSourceUrl" @error="status = Status.ERROR" />-->
        <img id="image" :src="mrIncredible" @error="status = Status.ERROR"/>
        <svg id="svgOverlay" ref="svgOverlay" style="position: absolute"></svg>
      </div>
    </div>
  </Window>
</template>
