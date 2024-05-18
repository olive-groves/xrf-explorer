<script setup lang="ts">
import { ref } from "vue";

import { Window } from "@/components/ui/window";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Separator } from "@/components/ui/separator";
import { useFetch } from "@vueuse/core";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

// Constants
const URL_IMAGE = "http://localhost:8001/api/get_overlay";
const URL_EMBEDDING = "http://localhost:8001/api/get_embedding";

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
const threshold = ref([100]);
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
    // Create URL for image
    const objectURL = URL.createObjectURL(data.value).toString();

    // Globally set the new URL
    imageSourceUrl.value = objectURL;

    // Update status
    status.value = Status.SUCCESS;
  } else {
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
    fetchDRImage();
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
    <!-- OVERLAY SECTION -->
    <div class="flex items-center" >
      <div class="block w-1"></div>
      <p class="font-bold">Overlay:</p>
    </div>
    <div class="block h-1"></div>
    <div class="flex items-center" >
      <div class="block w-1"></div>
      <Select v-model="selectedOverlay">
        <SelectTrigger class="w-32">
          <SelectValue placeholder="Select an overlay" />
        </SelectTrigger>
        <SelectContent>
          <SelectGroup>
            <SelectLabel>Overlays</SelectLabel>
            <SelectItem value="rgb">
              RGB
            </SelectItem>
            <SelectItem value="uv">
              UV
            </SelectItem>
            <SelectItem value="xray">
              XRay
            </SelectItem>
            <SelectItem value="0">
              Element 0
            </SelectItem>
            <SelectItem value="1">
              Element 1
            </SelectItem>
            <SelectItem value="9">
              Element 9
            </SelectItem>
          </SelectGroup>
        </SelectContent>
      </Select>
      <div class="block w-4"></div>
      <Button class="block w-28" @click="fetchDRImage">Show overlay</Button>
    </div>
    <div class="block h-2"></div>
    <!-- PARAMETERS SECTIONS -->
    <div class="flex items-center">
      <div class="block w-1"></div>
      <Separator class="w-64"/>
    </div>
    <div class="block h-2"></div>
    <div class="flex items-center">
      <div class="block w-1"></div>
      <p class="font-bold">Parameters:</p>
    </div> 
    <div class="block h-1"></div>
    <div class="flex items-center" >
      <div class="block w-1"></div>
      <Slider class="w-64" v-model="threshold" id="threshold" :min="0" :max="255" :step="1"/> 
    </div>
    <div class="flex items-center">
    <div class="block w-1"></div>
    <FormDescription>
      <span class="italic text-xs">Threshold value: </span>
      <span class="italic text-xs">{{ threshold?.[0] }}</span>
    </FormDescription>
    </div>
    <div class="block h-1"></div>
    <div class="flex items-center">
      <div class="block w-1"></div>
      <Select v-model="selectedElement">
        <SelectTrigger class="w-32">
          <SelectValue placeholder="Select an element" />
        </SelectTrigger>
        <SelectContent>
          <SelectGroup>
            <SelectLabel>Elements</SelectLabel>
            <SelectItem value="0">
              Element 0
            </SelectItem>
            <SelectItem value="1">
              Element 1
            </SelectItem>
            <SelectItem value="9">
              Element 9
            </SelectItem>
          </SelectGroup>
        </SelectContent>
      </Select>
      <div class="block w-4"></div>
      <Button class="block w-28" @click="updateEmbedding">Generate</Button>
    </div>
    <div class="block h-2"></div>
    <!-- GENERATION OF THE IMAGE -->
    <div class="flex items-center">
      <div class="block w-1"></div>
      <Separator class="w-64"/>
    </div>
    <div class="block h-2"></div>
    <div class="flex items-center" >
      <div class="block w-1"></div>
      <p class="font-bold">Generated image:</p>
    </div>
    <div class="block h-1"></div>
    <div class="flex items-center" >
      <div class="block w-1"></div>
      <span v-if="status == Status.LOADING">Loading...</span>
      <span v-if="status == Status.GENERATING">Generating...</span>
      <span v-if="status == Status.ERROR">{{ currentError }}</span>
      <img v-if="status == Status.SUCCESS" :src="imageSourceUrl" @error="status = Status.ERROR" />
    </div>
  </Window>
</template>