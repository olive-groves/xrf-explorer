<script setup lang="ts">
import { computed, inject, ref, watch } from "vue";
import { appState, datasource, elements } from "@/lib/appState";
import { useFetch } from "@vueuse/core";
import { FrontendConfig } from "@/lib/config";
import { ContextualImage } from "@/lib/workspace";
import { LassoSelect, LoaderPinwheel, SquareMousePointer } from "lucide-vue-next";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "vue-sonner";
import { exportableElements } from "@/lib/export";
import { updateMiddleImage } from "@/components/image-viewer/drSelectionHelper";
import { SelectionArea } from "@/components/ui/selection-area";
import { Separator } from "@/components/ui/separator";
import { SelectionAreaType } from "@/lib/selection";
import { remToPx } from "@/lib/utils";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import {
  NumberField,
  NumberFieldContent,
  NumberFieldDecrement,
  NumberFieldIncrement,
  NumberFieldInput,
} from "@/components/ui/number-field";

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
const currentError = ref("Unknown error");

// Dimensionality reduction parameters
const threshold = ref(100);
const selectedElement = ref();
const selectedOverlay = ref();

// Dimensionality reduction image
const imageSourceUrl = ref();

// Selection
const selectionAreaType = ref<SelectionAreaType>(SelectionAreaType.Rectangle);

/**
 * Fetch the dimensionality reduction image
 * Sets status to corresponding value
 * For the rest it uses the fetchBlob function.
 */
async function fetchDRImage() {
  // Check if the user specified an overlay
  if (selectedOverlay.value == null) {
    currentError.value = "Please select an overlay";
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
    currentError.value = "Failed to load overlay, make sure embedding has been generated";
    status.value = Status.ERROR;
  }
}

/**
 * Compute the embedding
 * Sets status to corresponding value
 * If embedding was generated successfully, it fetches the new image.
 */
async function updateEmbedding() {
  // Check if the DR Window is in the correct state
  if (status.value == Status.GENERATING) {
    toast.warning("Embedding is currently already being generated");
    return;
  } else if (status.value == Status.LOADING) {
    toast.warning("Embedding generation can not be started while overlay is being loaded");
    return;
  }

  // Check if an element was selected, if not return message to user.
  if (selectedElement.value == null) {
    currentError.value = "Please select an element";
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
  currentError.value = "Generating embedding failed";
  status.value = Status.ERROR;
}
</script>

<template>
  <Window title="Dimensionality reduction" location="left">
    <div class="space-y-2 p-2">
      <!-- EMBEDDING GENERATION -->
      <p class="-mb-2 font-bold">Embedding</p>
      <div class="flex space-x-2">
        <div class="grow space-y-1">
          <Label for="embedding_element">Element</Label>
          <Select v-model="selectedElement" id="embedding_element" class="w-full">
            <SelectTrigger>
              <SelectValue placeholder="Select an element" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem v-for="element in elements" :key="element.channel" :value="element.channel.toString()">
                {{ element.name }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div class="w-28 shrink-0 space-y-1">
          <Label for="embedding_threshold">Threshold</Label>
          <NumberField
            v-model="threshold"
            :min="0"
            :max="255"
            :step="1"
            id="embedding_threshold"
            :format-options="{
              minimumIntegerDigits: 1,
              maximumFractionDigits: 0,
            }"
          >
            <NumberFieldContent>
              <NumberFieldDecrement />
              <NumberFieldInput />
              <NumberFieldIncrement />
            </NumberFieldContent>
          </NumberField>
        </div>
      </div>
      <Button class="w-full" @click="updateEmbedding">Generate embedding</Button>

      <!-- OVERLAY SECTION -->
      <div class="space-y-1">
        <p class="font-bold">Overlay</p>
        <Select v-model="selectedOverlay" @update:model-value="fetchDRImage">
          <SelectTrigger>
            <SelectValue placeholder="Select an overlay" />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectLabel>Contextual images</SelectLabel>
              <SelectItem v-for="image in contextualImages" :key="image.name" :value="'contextual_' + image.name">
                {{ image.name }}
              </SelectItem>
            </SelectGroup>
            <SelectGroup>
              <SelectLabel>Elements</SelectLabel>
              <SelectItem v-for="element in elements" :key="element.channel" :value="'elemental_' + element.channel">
                {{ element.name }}
              </SelectItem>
            </SelectGroup>
          </SelectContent>
        </Select>
      </div>

      <!-- GENERATION OF THE IMAGE -->
      <div class="flex flex-col items-center justify-center space-y-2 rounded-md border p-8 text-center" ref="output">
        <span v-if="status == Status.WELCOME">Generate an embedding and choose an overlay</span>
        <span v-if="status == Status.LOADING">Loading</span>
        <span v-if="status == Status.GENERATING">Generating</span>
        <span v-if="status == Status.ERROR">{{ currentError }}</span>
        <div v-if="status == Status.LOADING || status == Status.GENERATING" class="size-6">
          <LoaderPinwheel class="size-full animate-spin" />
        </div>
        <div class="relative" v-if="status == Status.SUCCESS">
          <img :src="imageSourceUrl" ref="embeddingImage" @error="status = Status.ERROR" />
          <SelectionArea
            v-model="appState.selection.dimensionalityReduction.area"
            :type="selectionAreaType"
            :click-margin="remToPx(2)"
            :x="0"
            :y="0"
            :w="256"
            :h="256"
          />
        </div>
      </div>

      <!-- TOOLBAR -->
      <div class="flex w-min rounded-md border p-1">
        <ToggleGroup v-model:model-value="selectionAreaType">
          <ToggleGroupItem class="size-8 p-2" title="Rectangle selection" :value="SelectionAreaType.Rectangle">
            <SquareMousePointer />
          </ToggleGroupItem>
          <ToggleGroupItem class="size-8 p-2" title="Lasso selection" :value="SelectionAreaType.Lasso">
            <LassoSelect />
          </ToggleGroupItem>
        </ToggleGroup>
        <Separator orientation="vertical" class="mx-1 h-8" />
        <Label title="Selection color" for="color_dr" class="size-8 rounded-md p-2 hover:bg-accent">
          <div
            for="color_dr"
            class="size-4 rounded-md border border-border"
            :style="{
              'background-color': appState.selection.dimensionalityReduction.color,
            }"
          />
        </Label>
        <Input
          class="hidden"
          :id="`color_dr`"
          default-value="#FFFFFF"
          @update:model-value="(value: string) => (appState.selection.dimensionalityReduction.color = value)"
          type="color"
        />
      </div>
    </div>
  </Window>
</template>
