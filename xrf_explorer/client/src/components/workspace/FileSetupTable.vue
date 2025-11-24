<script setup lang="ts">
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { FileSetupTableRow, FileUploadDialog } from ".";
import { WorkspaceConfig } from "@/lib/workspace";
import { useFetch } from "@vueuse/core";
import { computed, inject, ref } from "vue";
// Lucide icons
import { Image, ImagePlus, AudioWaveform, Atom, Trash2 } from "lucide-vue-next";
import { FrontendConfig } from "@/lib/config";
import { ScrollArea } from "../ui/scroll-area";

enum DataComponentType {
  BaseImage = "baseImage",
  ContextualImage = "contextualImages",
  Spectral_Datacube = "spectralCubes",
  Elemental_Datacube = "elementalCubes",
}

// Inject the frontend configuration
const config = inject<FrontendConfig>("config")!;

// Define the workspace model
const model = defineModel<WorkspaceConfig>({ required: true });

// Variable for the type of element to add
const addElementType = ref("contextual_image");

// Variables for fetching and filtering files
const fileUrl = computed(() => `${config.api.endpoint}/${model.value.name}/files`);
const fileFetch = useFetch<string>(fileUrl);
const files = computed<string[]>(() => JSON.parse(fileFetch.data.value ?? "[]"));
const imageFiles = computed(() => filterByExtension(files.value, ["tif", "tiff", "png", "jpg", "jpeg", "bmp"]));
const recipeFiles = computed(() => filterByExtension(files.value, ["csv"]));
const rawFiles = computed(() => filterByExtension(files.value, ["raw"]));
const rplFiles = computed(() => filterByExtension(files.value, ["rpl"]));
const elementalFiles = computed(() => filterByExtension(files.value, ["csv", "dms"]));

// Delete functionality
const showDeleteFileDialog = ref(false);
const showDeleteComponentDialog = ref(false);
const showMultiDeleteDialog = ref(false);
const selectedFilesToDelete = ref<string[]>([]);

const componentNameToDelete = ref("");
const componentTypeToDelete = ref<DataComponentType>();

// All files in the project folder (from server), excluding workspace.json
const allProjectFiles = computed(() => {
  return (files.value || []).filter((file) => file.toLowerCase() !== "workspace.json");
});

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
    // Add a new contextual image
    case "contextual_image": {
      model.value.contextualImages.push({
        imageLocation: "",
        name: "",
        recipeLocation: "",
      });
      break;
    }
    // Add a new spectral datacube
    case "spectral_cube": {
      model.value.spectralCubes.push({
        name: "",
        rawLocation: "",
        rplLocation: "",
        recipeLocation: "",
      });
      break;
    }
    // Add a new elemental datacube
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
 * Removes a component from the workspace model.
 * @param componentName The component names to be removed from the workspace.
 * @param componentType The component type to be removed.
 */
async function removeComponentsFromWorkspace(componentName: string, componentType?: DataComponentType) {
  if (componentType == undefined) {
    console.error("Could not delete component " + componentName);
    return;
  }

  switch (componentType) {
    case DataComponentType.BaseImage:
      model.value.baseImage.imageLocation = "";
      break;

    case DataComponentType.ContextualImage:
      model.value.contextualImages = model.value.contextualImages.filter((img) => img.name !== componentName);
      break;

    case DataComponentType.Spectral_Datacube:
      model.value.spectralCubes = model.value.spectralCubes.filter((img) => img.name !== componentName);
      break;

    case DataComponentType.Elemental_Datacube:
      model.value.elementalCubes = model.value.elementalCubes.filter((img) => img.name !== componentName);
      break;
  }

  // Refresh the file list from server
  await fileFetch.execute();

  // Update workspace.json with the modified model
  const workspaceResponse = await fetch(`${config.api.endpoint}/${model.value.name}/workspace`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(model.value),
  });

  if (!workspaceResponse.ok) {
    console.error("Failed to update workspace.json:", workspaceResponse.statusText);
  }

  showDeleteComponentDialog.value = false;
}

/**
 * Remove file from component.
 * @param filename The file to be removed from the component, if it exists anywhere.
 */
async function removeFileFromComponent(filename: string) {
  console.log("Removing file: " + filename);

  if (model.value.baseImage.name == filename) {
    model.value.baseImage.name == "";
  }

  model.value.contextualImages = model.value.contextualImages.map((img) => ({
    ...img,
    imageLocation: img.imageLocation === filename ? "" : img.imageLocation,
    recipeLocation: img.recipeLocation === filename ? "" : img.recipeLocation,
  }));

  model.value.spectralCubes = model.value.spectralCubes.map((img) => ({
    ...img,
    imageLocation: img.rawLocation === filename ? "" : img.rawLocation,
    recipeLocation: img.recipeLocation === filename ? "" : img.recipeLocation,
  }));

  model.value.elementalCubes = model.value.elementalCubes.map((img) => ({
    ...img,
    imageLocation: img.dataLocation === filename ? "" : img.dataLocation,
    recipeLocation: img.recipeLocation === filename ? "" : img.recipeLocation,
  }));
}

/**
 * Delete the files from the workspace and the server.
 */
async function handleMultiDeleteConfirmed() {
  console.log("Remove files:");
  try {
    console.log(selectedFilesToDelete.value);

    // Use the new batch delete endpoint - note the endpoint name matches your backend
    const response = await fetch(`${config.api.endpoint}/${model.value.name}/delete_files`, {
      method: "DELETE", // Your backend supports both DELETE and POST
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filenames: selectedFilesToDelete.value }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Failed to delete files:", response.status, errorText);
      return;
    }

    const result = await response.json();
    console.log(`Successfully deleted ${result.deleted.length} files`);

    if (result.failed.length > 0) {
      console.warn("Some files failed to delete:", result.failed);
      // Optionally show user which files failed to delete
    }

    for (const filename in result.deleted) {
      removeFileFromComponent(result.deleted[filename]);
    }
    //removeComponentsFromWorkspace();
  } catch (error) {
    console.error("Error during multi-delete:", error);
  }

  selectedFilesToDelete.value = [];
  showMultiDeleteDialog.value = false;
  showDeleteFileDialog.value = false;
}
</script>

<template>
  <div>
    <!-- Header -->
    <div class="grid grid-cols-[2rem,12rem,1fr,2rem] place-items-center gap-2">
      <div class="col-start-2 place-self-start">Name</div>
      <div class="col-start-3 place-self-start">Files</div>
    </div>

    <Separator class="mt-2" />

    <!-- Content -->
    <ScrollArea class="mr-[-0.8125rem] h-[32rem] pr-[0.8125rem]">
      <div class="grid grid-cols-[2rem,12rem,1fr,2rem] place-items-center gap-2 pt-2">
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
          <Button
            variant="destructive"
            class="row-span-2 size-full p-2"
            @click="
              showDeleteComponentDialog = true;
              componentNameToDelete = image.name;
              componentTypeToDelete = DataComponentType.ContextualImage;
            "
          >
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
          <Button
            variant="destructive"
            class="row-span-3 size-full p-2"
            @click="
              showDeleteComponentDialog = true;
              componentNameToDelete = cube.name;
              componentTypeToDelete = DataComponentType.Spectral_Datacube;
            "
          >
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
          <Button
            variant="destructive"
            class="row-span-2 size-full p-2"
            @click="
              showDeleteComponentDialog = true;
              componentNameToDelete = cube.name;
              componentTypeToDelete = DataComponentType.Elemental_Datacube;
            "
          >
            <Trash2 />
          </Button>
          <FileSetupTableRow type="a recipe" :options="recipeFiles" v-model="cube.recipeLocation" />
        </template>
      </div>
      <!-- Delete confirmation dialog -->
      <div v-if="showDeleteComponentDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
        <div class="min-w-[320px] rounded-lg bg-background p-6 text-foreground shadow-lg">
          <div class="mb-2 text-lg font-bold">Confirm Deletion</div>
          <div class="mb-4 text-sm text-muted-foreground">
            Are you sure you want to delete this component from the workspace? This action cannot be undone.
          </div>
          <div class="flex justify-end space-x-2">
            <Button variant="outline" @click="showDeleteComponentDialog = false">Cancel</Button>
            <Button
              variant="destructive"
              @click="removeComponentsFromWorkspace(componentNameToDelete, componentTypeToDelete)"
              >Delete</Button
            >
          </div>
        </div>
      </div>
    </ScrollArea>

    <Separator class="mb-2" />

    <!-- Footer -->
    <div class="flex justify-between">
      <div class="flex space-x-2">
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
        <Button @click="addElementToWorkspace()" variant="outline">Add component</Button>
      </div>
      <div class="flex space-x-2">
        <FileUploadDialog :data-source="model.name" @files-uploaded="fileFetch.execute()" />
        <Button variant="destructive" @click="showMultiDeleteDialog = true"> Delete Selected </Button>
      </div>
    </div>

    <!-- Multi delete dialog -->
    <div v-if="showMultiDeleteDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div class="max-h-[500px] min-w-[360px] overflow-y-auto rounded-lg bg-background p-6 text-foreground shadow-lg">
        <div class="mb-2 text-lg font-bold">Delete Files</div>
        <div class="mb-4 text-sm text-muted-foreground">Select the files you want to delete from this project.</div>
        <div class="mb-4 space-y-2">
          <label v-for="file in allProjectFiles" :key="file" class="flex items-center space-x-2">
            <input type="checkbox" :value="file" v-model="selectedFilesToDelete" class="form-checkbox" />
            <span class="truncate">{{ file }}</span>
          </label>
        </div>
        <div class="flex justify-end space-x-2">
          <Button variant="outline" @click="showMultiDeleteDialog = false">Cancel</Button>
          <Button
            variant="destructive"
            :disabled="selectedFilesToDelete.length === 0"
            @click="showDeleteFileDialog = true"
          >
            Delete Selected
          </Button>
        </div>
      </div>
    </div>

    <!-- Delete confirmation dialog -->
    <div v-if="showDeleteFileDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div class="min-w-[320px] rounded-lg bg-background p-6 text-foreground shadow-lg">
        <div class="mb-2 text-lg font-bold">Confirm Deletion</div>
        <div class="mb-4 text-sm text-muted-foreground">
          Are you sure you want to delete these files? This action cannot be undone.
        </div>
        <div class="flex justify-end space-x-2">
          <Button variant="outline" @click="showDeleteFileDialog = false">Cancel</Button>
          <Button variant="destructive" @click="handleMultiDeleteConfirmed">Delete</Button>
        </div>
      </div>
    </div>
  </div>
</template>
