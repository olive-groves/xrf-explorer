<script setup lang="ts">
import { ref, watch } from "vue";
import { datasource } from "@/lib/appState";
import { inject } from "vue";
import { useFetch } from "@vueuse/core";
import { FrontendConfig } from "@/lib/config";
import { LoaderPinwheel } from "lucide-vue-next";
import { LabeledSlider } from "@/components/ui/slider";
import { exportableElements } from "@/lib/export";

// Setup output for export
const output = ref<HTMLElement>();
watch(output, (value) => (exportableElements["DR Overlay"] = value));

// Constants
const config = inject<FrontendConfig>("config")!;
const URL_IMAGE = `${config.api.endpoint}/get_dr_overlay`;
const URL_EMBEDDING = `${config.api.endpoint}/get_dr_embedding`;

// Status dimensionaility reduction
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
  const url = new URL(URL_IMAGE);
  url.searchParams.set("type", selectedOverlay.value.toString());
  url.searchParams.set("dataSource", datasource.value);

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
  _url.searchParams.set("dataSource", datasource.value);

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
              <SelectItem value="0"> Element 0 </SelectItem>
              <SelectItem value="1"> Element 1 </SelectItem>
              <SelectItem value="9"> Element 9 </SelectItem>
            </SelectGroup>
          </SelectContent>
        </Select>
        <Button class="ml-2 w-40" @click="updateEmbedding">Generate</Button>
      </div>
      <!-- GENERATION OF THE IMAGE -->
      <p class="mt-4 font-bold">Generated image:</p>
      <div class="mt-1 flex aspect-square flex-col items-center justify-center space-y-2 text-center" ref="output">
        <span v-if="status == Status.WELCOME">Choose your overlay and paramaters and start the generation.</span>
        <span v-if="status == Status.LOADING">Loading</span>
        <span v-if="status == Status.GENERATING">Generating</span>
        <span v-if="status == Status.ERROR">{{ currentError }}</span>
        <div v-if="status == Status.LOADING || status == Status.GENERATING" class="size-6">
          <LoaderPinwheel class="size-full animate-spin" />
        </div>
        <img v-if="status == Status.SUCCESS" :src="imageSourceUrl" @error="status = Status.ERROR" />
      </div>
    </div>
  </Window>
</template>
