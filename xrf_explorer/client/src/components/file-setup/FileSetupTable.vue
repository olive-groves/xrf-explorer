<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { FileSetupTableRow, FileUploadDialog } from ".";
import { WorkspaceConfig } from "@/lib/workspace";
import { useFetch } from "@vueuse/core";
import { computed, inject, ref } from "vue";
import { Image, ImagePlus, AudioWaveform, Atom, Trash2 } from "lucide-vue-next";
import { FrontendConfig } from "@/lib/config";

const config = inject<FrontendConfig>("config")!;

const model = defineModel<WorkspaceConfig>({ required: true });

const addElementType = ref("contextual_image");

const fileUrl = computed(() => `${config.api.endpoint}/${model.value.name}/files`);
const fileFetch = useFetch<string>(fileUrl);
const files = computed<string[]>(() => JSON.parse(fileFetch.data.value ?? "[]"));
const imageFiles = computed(() => filterByExtension(files.value, ["tif", "tiff", "png", "jpg", "jpeg", "bmp"]));
const recipeFiles = computed(() => filterByExtension(files.value, ["csv"]));
const rawFiles = computed(() => filterByExtension(files.value, ["raw"]));
const rplFiles = computed(() => filterByExtension(files.value, ["rpl"]));
const elementalFiles = computed(() => filterByExtension(files.value, ["csv", "dms"]));

/**
 * Filters a list of filenames to only include files with the specified extensions.
 * @param filenames - The filenames to filter.
 * @param extensions - The allowed extensions.
 * @param empty - Add an empty filename to the list.
 * @returns The filtered list of filenames.
 */
function filterByExtension(filenames: string[], extensions: string[], empty: boolean = false) {
  const names = filenames.filter((file) => {
    const parts = file.split(".");
    const extension = parts[parts.length - 1].toLowerCase();
    return extensions.includes(extension);
  });
  if (empty) names.unshift("");
  return names;
}

/**
 * Adds a component of the type specified by addElementType to the workspace model.
 */
function addElementToWorkspace() {
  const elementType = addElementType.value;

  switch (elementType) {
    case "contextual_image": {
      model.value.contextualImages.push({
        imageLocation: "",
        name: "",
        recipeLocation: "",
      });
      break;
    }
    case "spectral_cube": {
      model.value.spectralCubes.push({
        name: "",
        rawLocation: "",
        rplLocation: "",
        recipeLocation: "",
      });
      break;
    }
    case "elemental_cube": {
      model.value.elementalCubes.push({
        name: "",
        dataLocation: "",
        recipeLocation: "",
      });
      break;
    }
  }
}

/**
 * Removes a specified element from the model.
 * @param type - The type of the element to remove.
 * @param name - The name of the element to remove.
 */
function removeElement(type: string, name: string) {
  switch (type) {
    case "contextual_image": {
      model.value.contextualImages = model.value.contextualImages.filter((value) => value.name != name);
      break;
    }
    case "spectral_cube": {
      model.value.spectralCubes = model.value.spectralCubes.filter((value) => value.name != name);
      break;
    }
    case "elemental_cube": {
      model.value.elementalCubes = model.value.elementalCubes.filter((value) => value.name != name);
      break;
    }
  }
}
</script>

<template>
  <div class="grid grid-cols-[min-content,min-content,1fr,2rem] place-items-center gap-2">
    <!-- Header -->
    <div />
    <div class="place-self-start">Name</div>
    <div class="place-self-start">Files</div>
    <div />
    <Separator class="col-span-full" />

    <!-- Base image -->
    <Image class="ml-2 size-6" title="Base image" />
    <Input placeholder="Name" v-model:model-value="model.baseImage.name" />
    <FileSetupTableRow type="an image" :options="imageFiles" v-model="model.baseImage.imageLocation" />
    <Separator class="col-span-full" />

    <!-- Contextual images -->
    <template v-for="(image, index) in model.contextualImages" :key="index">
      <ImagePlus class="ml-2 size-6" title="Contextual image" />
      <Input placeholder="Name" v-model:model-value="image.name" />
      <FileSetupTableRow type="an image" :options="imageFiles" v-model="image.imageLocation" />
      <Button variant="destructive" class="size-8 p-2" @click="removeElement('contextual_image', image.name)">
        <Trash2 />
      </Button>
      <FileSetupTableRow type="a recipe" :options="recipeFiles" v-model="image.recipeLocation" />
      <Separator class="col-span-full" />
    </template>

    <!-- Spectral datacubes -->
    <template v-for="(cube, index) in model.spectralCubes" :key="index">
      <AudioWaveform class="ml-2 size-6" title="Spectral datacube" />
      <Input placeholder="Name" v-model:model-value="cube.name" />
      <FileSetupTableRow type="a raw" :options="rawFiles" v-model="cube.rawLocation" />
      <Button variant="destructive" class="size-8 p-2" @click="removeElement('spectral_cube', cube.name)">
        <Trash2 />
      </Button>
      <FileSetupTableRow type="an rpl" :options="rplFiles" v-model="cube.rplLocation" />
      <FileSetupTableRow type="a recipe" :options="recipeFiles" v-model="cube.recipeLocation" />
      <Separator class="col-span-full" />
    </template>

    <!-- Elemental datacubes -->
    <template v-for="(cube, index) in model.elementalCubes" :key="index">
      <Atom class="ml-2 size-6" title="Elemental datacube" />
      <Input placeholder="Name" v-model:model-value="cube.name" />
      <FileSetupTableRow type="a data" :options="elementalFiles" v-model="cube.dataLocation" />
      <Button variant="destructive" class="size-8 p-2" @click="removeElement('elemental_cube', cube.name)">
        <Trash2 />
      </Button>
      <FileSetupTableRow type="a recipe" :options="recipeFiles" v-model="cube.recipeLocation" />
      <Separator class="col-span-full" />
    </template>

    <!-- Footer -->
    <Select v-model:model-value="addElementType">
      <SelectTrigger class="col-start-2 w-48">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem default value="contextual_image">Contextual image</SelectItem>
        <SelectItem default value="spectral_cube">Spectral datacube</SelectItem>
        <SelectItem default value="elemental_cube">Elemental datacube</SelectItem>
      </SelectContent>
    </Select>
    <div class="flex w-full justify-between">
      <Button @click="addElementToWorkspace()" variant="outline">Add element</Button>
      <FileUploadDialog @files-uploaded="fileFetch.execute()" />
    </div>
  </div>
</template>
