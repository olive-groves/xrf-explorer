<script setup lang="ts">
import { computed, inject, ref, watch } from "vue";
import { appState, datasource, elements } from "@/lib/appState";
import { useFetch } from "@vueuse/core";
import { FrontendConfig } from "@/lib/config";
import { ContextualImage } from "@/lib/workspace";
import { LoaderPinwheel } from "lucide-vue-next";
import { LabeledSlider } from "@/components/ui/slider";
import { toast } from "vue-sonner";
import { Point2D } from "@/lib/utils";
import { LassoSelectionTool } from "@/lib/selection";
import * as d3 from "d3";
import { exportableElements } from "@/lib/export";
import { updateMiddleImage } from "@/components/image-viewer/drSelectionHelper";

// Setup output for export
const output = ref<HTMLElement>();
watch(output, (value) => (exportableElements["Embedding"] = value), { immediate: true });

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
const svgOverlay = ref<HTMLElement>();
const selectionTool: LassoSelectionTool = new LassoSelectionTool();

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

    // the middle image used for conversion from embedding to main viewer image needs to be updated
    updateMiddleImage();

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
    return;
  }

  // Set status to error
  currentError.value = "Generating embedding failed.";
  status.value = Status.ERROR;
}

/**
 * Handle the event where the user cancels the current selection.
 */
function cancelSelection() {
  selectionTool.cancelSelection();
}

/**
 * Handle the event where the user confirms the current selection.
 */
function confirmSelection() {
  selectionTool.confirmSelection();
}

/**
 * Handle mouse events when the mouse is clicked.
 * @param event - The mouse event.
 */
function onMouseDown(event: MouseEvent) {
  if (event.button == config.selectionTool.cancelButton) cancelSelection();
  else if (event.button == config.selectionTool.addPointButton) {
    const svg: HTMLElement | undefined = svgOverlay.value;
    if (svg != undefined) {
      // compute the position of the click relative to the SVG based on the client coordinates
      const clickedPos = {
        x: event.clientX - svg.getBoundingClientRect().left,
        y: event.clientY - svg.getBoundingClientRect().top,
      };
      selectionTool.addPointToSelection(clickedPos);
    }
  } else if (event.button == config.selectionTool.confirmButton) confirmSelection();

  updateSelectionVisuals();
}

/**
 * Handle keyboard events when the user presses a key.
 * @param event - The keyboard event.
 */
function onKeyDown(event: KeyboardEvent) {
  if (event.key == config.selectionTool.cancelKey) cancelSelection();
  else if (event.key == config.selectionTool.confirmKey) confirmSelection();

  updateSelectionVisuals();
}

/**
 * Update the visual representation of the selection in the embedding image and in the main viewer.
 */
function updateSelectionVisuals() {
  // update the embedding's SVG overlay
  drawSelection();

  // relay information to the image viewer
  if (!selectionTool.activeSelection) {
    console.info("Confirmed selection with " + selectionTool.selectedPoints.length + " points.");
    communicateSelectionWithImageViewer();
  }
}

/**
 * Draw the shape of the selection on the SVG overlay.
 */
function drawSelection() {
  // if the image is not found, drawing on an SVG of dimensions 0 will simply clear the SVG.
  const imageDimensions: { x: number; y: number; width: number; height: number } = {
    x: 0,
    y: 0,
    width: 0,
    height: 0,
  };

  const image: HTMLElement | null = document.getElementById("image");

  if (image == null) console.warn("Tried to draw selection but could not find image element in DR window.");
  else {
    // update dimensions with image element values to fit the SVG to the image
    const rect = image.getBoundingClientRect();
    imageDimensions.x = rect.left;
    imageDimensions.y = rect.top;
    imageDimensions.width = rect.width;
    imageDimensions.height = rect.height;
  }

  selectionTool.draw(d3.select("svgOverlay"), imageDimensions);
}

/**
 * Send the relevant information about the selection to the image viewer.
 */
async function communicateSelectionWithImageViewer() {
  const image: HTMLElement | null = document.getElementById("image");
  if (image == null) {
    console.warn("Tried to update the image to embedding cropping but could not find image element in DR window.");
    return;
  }
  const rect = image.getBoundingClientRect(); // get the dimensions of the current window on the client

  // communicate the information to the image viewer using the app's state (selection is scaled down to a 256x256 image)
  appState.selection.dimensionalityReduction = {
    selectionType: selectionTool.type(),
    points: selectionTool.selectedPoints.map((point: Point2D) => ({
      x: Math.round((point.x * 255) / rect.width),
      y: Math.round((point.y * 255) / rect.height),
    })),
  };
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
            <SelectValue placeholder="Select an overlay" />
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
      <LabeledSlider label="Threshold" v-model="threshold" :min="0" :max="255" :step="1" :default="[100]" />
      <div class="mt-1 flex items-center">
        <Select v-model="selectedElement">
          <SelectTrigger>
            <SelectValue placeholder="Select an element" />
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
        class="pointer-events-auto mt-1 flex aspect-square flex-col items-center justify-center space-y-2 text-center"
        style="cursor: crosshair; position: relative"
        @mousedown="onMouseDown"
        tabindex="0"
        @keyup="onKeyDown"
        id="imageContainer"
        ref="output"
      >
        <div class="mt-1 flex aspect-square flex-col items-center justify-center space-y-2 text-center" ref="output">
          <span v-if="status == Status.WELCOME">Choose your overlay and parameters and start the generation.</span>
          <span v-if="status == Status.LOADING">Loading</span>
          <span v-if="status == Status.GENERATING">Generating</span>
          <span v-if="status == Status.ERROR">{{ currentError }}</span>
          <div v-if="status == Status.LOADING || status == Status.GENERATING" class="size-6">
            <LoaderPinwheel class="size-full animate-spin" />
          </div>
          <img v-if="status == Status.SUCCESS" :src="imageSourceUrl" id="image" @error="status = Status.ERROR" />
          <svg
            v-if="status == Status.SUCCESS"
            id="svgOverlay"
            ref="svgOverlay"
            @error="status = Status.ERROR"
            style="position: absolute"
          ></svg>
        </div>
      </div>
    </div>
  </Window>
</template>
