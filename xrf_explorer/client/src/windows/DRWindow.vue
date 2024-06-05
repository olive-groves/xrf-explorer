<script setup lang="ts">
import { computed, inject, ref } from "vue";
import { appState, datasource, elements } from "@/lib/appState";
import { useFetch } from "@vueuse/core";
import { FrontendConfig } from "@/lib/config";
import { ContextualImage } from "@/lib/workspace";
import { LabeledSlider } from "@/components/ui/slider";
import { toast } from "vue-sonner";
import { Point2D } from "@/components/image-viewer/types";
import { SelectionOption, SelectionTool } from "@/components/functional/selection/selection_tool.ts";
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
const selectionTool: SelectionTool = new SelectionTool(SelectionOption.Rectangle);
let imageToEmbeddingCropping: {
  xEmbedRange: number[], yEmbedRange: number[],
  xPlotRange: number[], yPlotRange: number[]
} = {
  xEmbedRange: [], yEmbedRange: [],
  xPlotRange: [], yPlotRange: [],
}
const mrIncredible: string = "src/windows/mr-incredible.png";

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
  const { response, data } = await useFetch(apiURL).get().blob();

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
  const { response, data } = await useFetch(apiURL).get().text();

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

    // Load the new values representing the difference between the image and the embedding
    await updateImageToEmbeddingCropping();
    return;
  }

  // Set status to error
  currentError.value = "Generating embedding failed.";
  status.value = Status.ERROR;
}

/**
 * Get the new values representing the difference in dimensions between the image and the embedding.
 */
async function updateImageToEmbeddingCropping() {
  fetch(`${config.api.endpoint}/${datasource.value}/dr/dimensions`).then(
      async (response) => {
        response.json().then(
            (dimensions) => {
              imageToEmbeddingCropping.xEmbedRange = dimensions.xembedrange;
              imageToEmbeddingCropping.yEmbedRange = dimensions.yembedrange;
              imageToEmbeddingCropping.xPlotRange = dimensions.xplotrange;
              imageToEmbeddingCropping.yPlotRange = dimensions.yplotrange;
            },
            () => toast.error("An error occurred while parsing the Dimensionality Reduction selection."),
        );
      },
      () => toast.error("An error occurred while parsing the Dimensionality Reduction selection."),
  );
}

function onMouseDown(event: MouseEvent) {

  if (event.button == config.selectionToolConfig.cancelButton)
    selectionTool.cancelSelection();

  else if (event.button == config.selectionToolConfig.addPointButton) {

    const svg: HTMLElement | null = document.getElementById("svgOverlay");
    if (svg != null) {
      // compute the position of the click relative to the SVG based on the client coordinates
      const clickedPos = {
        x: event.clientX - svg.getBoundingClientRect().left,
        y: event.clientY - svg.getBoundingClientRect().top
      };
      selectionTool.addPointToSelection(clickedPos);
    }
  }

  else if (event.button == config.selectionToolConfig.confirmButton)
    selectionTool.confirmSelection();

  // update the SVG overlay
  drawSelection();

  // relay information to the image viewer
  if (selectionTool.finishedSelection) {
    console.info("Confirmed selection with " + selectionTool.selectedPoints.length + " points.");
    communicateSelectionWithImageViewer();
  }
}

/**
 * Send the relevant information about the selection to the image viewer.
 */
async function communicateSelectionWithImageViewer() {
  let selectionPointsInEmbedding: Point2D[] = [];
  // update the selection points' coordinates to the embedding's coordinates;
  if (selectionTool.selectedPoints.length != 0) getSelectionAsEmbeddingDimensions(selectionPointsInEmbedding);
  // communicate the relevant information to the image viewer using the app's state
  appState.selection.drSelection = {
    selectionType: selectionTool.selectionType,
    points: selectionPointsInEmbedding,
    embeddedImageDimensions: {
      width: imageToEmbeddingCropping.xEmbedRange[1] - imageToEmbeddingCropping.xEmbedRange[0],
      height: imageToEmbeddingCropping.yEmbedRange[1] - imageToEmbeddingCropping.yEmbedRange[0] },
  };
}

/**
 * The image element on which the embedding is plotted has larger dimensions than the embedding itself, here we update
 * the coordinates of the selection to fit the embedding's dimensions instead of the image's.
 */
function getSelectionAsEmbeddingDimensions(writeList: Point2D[]) {
  // compute cropping
  const xDelta: number = imageToEmbeddingCropping.xEmbedRange[0] - imageToEmbeddingCropping.xPlotRange[0];
  const xMin: number = imageToEmbeddingCropping.xEmbedRange[0];
  const xMax: number = imageToEmbeddingCropping.xPlotRange[1] - imageToEmbeddingCropping.xEmbedRange[1];
  const yMin: number = imageToEmbeddingCropping.yEmbedRange[0];
  const yDelta: number = imageToEmbeddingCropping.yEmbedRange[0] - imageToEmbeddingCropping.yPlotRange[0];
  const yMax: number = imageToEmbeddingCropping.yPlotRange[1] - imageToEmbeddingCropping.yEmbedRange[1];

  // adapt the coordinates of the selected points to the cropped embedding
  for (const point of selectionTool.selectedPoints) {
    const newPoint: Point2D = { x: point.x, y: point.y };
    // crop left side
    if (newPoint.x < xMin) newPoint.x = xMin;
    else newPoint.x -= xDelta;

    // crop right side
    if (newPoint.x > xMax) newPoint.x = xMax;

    // crop top side
    if (newPoint.y < yMin) newPoint.y = yMin;
    else newPoint.y -= yDelta;

    // crop bottom side
    if (newPoint.y > yMax) newPoint.y = yMax;

    writeList.push(newPoint);
  }
}

/**
 * Draw the shape of the selection on the SVG overlay
 */
function drawSelection() {

  // if the image is not found, drawing on an SVG of dimensions 0 will simply clear the SVG.
  const imageDimensions: { x: number, y: number, width: number, height: number } = {
    x: 0,
    y: 0,
    width: 0,
    height: 0
  }

  const image: HTMLElement | null = document.getElementById("image");

  if (image == null)
    console.error("Tried to draw selection but could not find image element in DR window.");
  else {
    // update dimensions with image element values to fit the SVG to the image
    const rect = image.getBoundingClientRect();
    imageDimensions.x = rect.left;
    imageDimensions.y = rect.top;
    imageDimensions.width = rect.width;
    imageDimensions.height = rect.height;
  }

  selectionTool.draw(d3.select(svgOverlay.value), imageDimensions, config);
}
</script>

<template>
  <Window title="Dimensionality reduction" location="left" @window-mounted="drawSelection">
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
