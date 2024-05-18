<script setup lang="ts">
import { ref } from "vue";

import { inject } from "vue";
import { Window } from "@/components/ui/window";
import { Button } from "@/components/ui/button";
import { useFetch } from "@vueuse/core";
import { FrontendConfig } from "@/lib/config";

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
}
const status = ref(Status.LOADING);
const currentError = ref("Error");

// Dimensionality reduction parameters
const threshold = ref(100);
const selectedElement = ref(9);
const selectedOverlay = ref("rgb");

// Dimensionality reduction image
const imageSourceUrl = ref("");

/**
 * Fetch the dimensionality reduction image
 * Sets status to corresponding value
 * For the rest it uses the fetchBlob function.
 */
async function fetchDRImage() {
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
  status.value = Status.GENERATING;

  // Create URL for embedding
  const _url = new URL(URL_EMBEDDING);
  _url.searchParams.set("element", selectedElement.value.toString());
  _url.searchParams.set("threshold", threshold.value.toString());

  // Create the embedding
  const data = await fetch(_url.toString());

  if (data.ok) {
    // Load the new embedding
    await fetchDRImage();
    return;
  }

  // Set status to error
  currentError.value = "Generating embedding failed.";
  status.value = Status.ERROR;
}

fetchDRImage();
</script>

<template>
  <Window title="Dimensionality reduction">
    <span v-if="status == Status.LOADING">Loading...</span>
    <span v-if="status == Status.GENERATING">Generating...</span>
    <span v-if="status == Status.ERROR">{{ currentError }}</span>
    <img v-if="status == Status.SUCCESS" :src="imageSourceUrl" @error="status = Status.ERROR" />

    <p>Overlays {{ selectedOverlay }}:</p>
    <select v-model="selectedOverlay">
      <option value="rgb">rgb</option>
      <option value="uv">uv</option>
      <option value="xray">xray</option>
      <option value="0">Element 0</option>
      <option value="1">Element 1</option>
      <option value="9">Element 9</option>
    </select>
    <br />
    <Button @click="fetchDRImage">Show overlay</Button>
    <p>Parameters:</p>
    <p>Threshold: {{ threshold }}</p>
    <input type="range" v-model="threshold" min="0" max="255" />
    <br />
    <p>Element: {{ selectedElement }}</p>
    <select v-model="selectedElement">
      <option value="0">Element 0</option>
      <option value="1">Element 1</option>
      <option value="9">Element 9</option>
    </select>
    <br />
    <Button @click="updateEmbedding">Generate</Button>
  </Window>
</template>
