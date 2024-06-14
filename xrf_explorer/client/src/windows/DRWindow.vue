<script setup lang="ts">
import { computed, inject, ref, watch } from "vue";
import { appState, datasource, elements } from "@/lib/appState";
import { useFetch } from "@vueuse/core";
import { FrontendConfig } from "@/lib/config";
import { ContextualImage } from "@/lib/workspace";
import { LoaderPinwheel } from "lucide-vue-next";
import { LabeledSlider } from "@/components/ui/slider";
import { toast } from "vue-sonner";
import { exportableElements } from "@/lib/export";
import { updateMiddleImage } from "@/components/image-viewer/drSelectionHelper";
import { SelectionArea } from "@/components/ui/selection-area";
import { SelectionAreaType } from "@/lib/selection";
import { remToPx } from "@/lib/utils";

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
</script>

<template>
  <Window title="Dimensionality reduction" location="left">
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
        style="position: relative"
        tabindex="0"
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
          <div class="relative m-8" v-if="status == Status.SUCCESS">
            <img :src="imageSourceUrl" ref="embeddingImage" @error="status = Status.ERROR" />
            <SelectionArea
              v-model="appState.selection.dimensionalityReduction"
              :type="SelectionAreaType.Lasso"
              :click-margin="remToPx(2)"
              :x="0"
              :y="0"
              :w="256"
              :h="256"
            />
          </div>
        </div>
      </div>
    </div>
  </Window>
</template>
