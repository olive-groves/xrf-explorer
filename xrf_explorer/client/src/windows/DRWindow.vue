<script setup lang="ts">
import { ref } from 'vue';

import { Window } from '@/components/ui/window';
import { Button } from '@/components/ui/button';

// Constants 
const URL_IMAGE = 'http://localhost:8001/api/get_overlay';
const URL_EMBEDDING = 'http://localhost:8001/api/get_embedding';

// Status dimensionaility reduction
enum Status {
  LOADING,
  GENERATING,
  ERROR,
  SUCCESS
}
const status = ref(Status.LOADING)
const currentError = ref("")

// Dimensionality reduction parameters
var threshold = ref(100)
var selectedElement = ref(9)
var selectedOverlay = ref("rgb")

// Dimensionality reduction image
const imageSourceUrl = ref("")

// Returns true if the blob was fetched successfully
// Sets error in currentError if an error occured
// Sets the image URL in imageSourceUrl
async function fetchBlob(url: string) {
  // Fetch the image
  const response = await fetch(url);
  var fetchSuccessful = false;

  // Check if fetching the image was successful
  if (response.ok) {
    // Success response. Now save the image locally
    fetchSuccessful = await response.blob()
      .then(myBlob => {
        // Create URL for image
        const objectURL = URL.createObjectURL(myBlob).toString();

        // Globally set the new URL
        imageSourceUrl.value = objectURL;

        return true
      })
      .catch(error => {
        console.log("Error: ", error)

        // Globally set error message
        currentError.value = "An error occured";

        return false
      })
  } else {
    // Error response
    fetchSuccessful = await response.text()
      .then((text) => {
        // Globally set error message
        currentError.value = text;

        return false
      })
      .catch((error) => {
        console.log("Error: ", error)

        // Globally set error message
        currentError.value = "An error occured";

        return false
      })
  }

  return fetchSuccessful
}

// Fetch the dimensionality reduction image
// Sets status to corresponding value
// For the rest it uses the fetchBlob function
async function fetchDRImage() {
  status.value = Status.LOADING;

  // Set the overlay type
  var url = new URL(URL_IMAGE);
  url.searchParams.set('type', selectedOverlay.value.toString());

  // Fetch the image
  const succes = await fetchBlob(url.toString());

  // Set the status
  if (succes) {
    status.value = Status.SUCCESS;
  } else {
    status.value = Status.ERROR;
  }
}

// Compute the embedding
// Sets status to corresponding value
// If embedding was generated successfully, it fetches the new image
async function updateEmbedding() {
  status.value = Status.GENERATING;

  // Create URL for embedding
  const _url = new URL(URL_EMBEDDING);
  _url.searchParams.set('element', selectedElement.value.toString());
  _url.searchParams.set('threshold', threshold.value.toString());

  // Create the embedding
  const data = await fetch(_url.toString());

  if (data.ok) {
    // Load the new embedding
    fetchDRImage()
  } else {
    // Show error message
    await data.text()
      .then((error) => currentError.value = error)
      .catch((error) => {
        console.log("Error: ", error)

        // Globally set error message
        currentError.value = "An error occured";
      })

    status.value = Status.ERROR;
  }
}

fetchDRImage()

</script>

<template>
  <Window title="Dimensionality reduction">
    <span v-if="status == Status.LOADING">Loading...</span>
    <span v-if="status == Status.GENERATING">Generating...</span>
    <span v-if="status == Status.ERROR">{{ currentError }}</span>
    <img v-if="status == Status.SUCCESS" :src="imageSourceUrl" @error="status = Status.ERROR">

    <p> Overlays {{ selectedOverlay }}: </p>
    <select v-model="selectedOverlay">
      <option value="rgb">rgb</option>
      <option value="0">Element 0</option>
      <option value="9">Element 9</option>
    </select>
    <br>
    <Button @click="fetchDRImage">Show overlay</Button>
    <p> Parameters: </p>
    <p>Threshold: {{ threshold }}</p>
    <input type="range" v-model="threshold" min=0 max=100>
    <br>
    <p>Element: {{ selectedElement }}</p>
    <select v-model="selectedElement">
      <option value="0">Element 0</option>
      <option value="1">Element 1</option>
      <option value="9">Element 9</option>
    </select>
    <br>
    <Button @click="updateEmbedding">Generate</Button>
  </Window>
</template>