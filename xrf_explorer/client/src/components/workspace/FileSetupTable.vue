<script setup lang="ts">
//import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { FileSetupTableRow, FileUploadDialog } from ".";
import { WorkspaceConfig } from "@/lib/workspace";
import { useFetch } from "@vueuse/core";
import { computed, inject, ref, onMounted, watch} from "vue";
// Lucide icons
import { Image, /*ImagePlus,*/ AudioWaveform, Atom, Trash2 } from "lucide-vue-next";
import { FrontendConfig } from "@/lib/config";
import { ScrollArea } from "../ui/scroll-area";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { appState } from "@/lib/appState";

// Inject the frontend configuration
const config = inject<FrontendConfig>("config")!;

// Define the workspace model
const model = defineModel<WorkspaceConfig>({ required: true });

// Variable wheter we are currently on the partial data screen
const UploadingPartialData = ref("full");

// Variables wheter we want to include spectral and/or elemental datacubes
const includeSpectral = ref(true);
const includeElemental = ref(true);

// Variables for fetching and filtering files
const fileUrl = computed(() => `${config.api.endpoint}/${model.value.name}/files`);
const fileFetch = useFetch<string>(fileUrl);
const files = computed<string[]>(() => JSON.parse(fileFetch.data.value ?? "[]"));
const imageFiles = computed(() => filterByExtension(files.value, ["tif", "tiff", "png", "jpg", "jpeg", "bmp"]));
const recipeFiles = computed(() => filterByExtension(files.value, ["csv"]));
const rawFiles = computed(() => filterByExtension(files.value, ["raw"]));
const rplFiles = computed(() => filterByExtension(files.value, ["rpl"]));
const elementalFiles = computed(() => filterByExtension(files.value, ["csv", "dms"]));


// On Element loading add one datacube element
onMounted(() => {
  addDatacube();
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
 * Called whenever we switch from partial data uploads to full data uploads
 * and vice verse. Adds a second data cube when going to partial datacubes.
 * Removes all but one datacube when switching to full single full datacube.
 * @param val - represent the new state, either "full" or "partial"
 * Partial =  Partial data scans
 * Full = Full data scan
 */
watch(UploadingPartialData, (val) => {
  if (val === "partial") {
    addDatacube();
    appState.stitching = true;
  } else {
    appState.stitching = false;
    if (model.value.spectralCubes.length > 1) {
      model.value.spectralCubes = [model.value.spectralCubes[0]];
    }
    if (model.value.elementalCubes.length > 1) {
      model.value.elementalCubes = [model.value.elementalCubes[0]];
    }
  }
});

/**
 * Adds both a spectral and elemental datacube element
 */
function addDatacube() {
  if (includeSpectral.value) {
    addElementToWorkspace("spectral_cube")
  }
  if (includeElemental.value) {
    addElementToWorkspace("elemental_cube")
  }
}

/**
 * Called whenever we switch from partial data uploads to full data uploads
 * and vice verse. Adds a second data cube when going to partial datacubes.
 * Removes all but one datacube when switching to full single full datacube.
 * @param type - Defines wheter the include spectral or include elemental checkbox has changed value
 * @param value - The new value of the checkbox
 */
function handleIncludeChange(type: "spectral" | "elemental", value: boolean) {
  if (!value) {
    // Remove all cubes of that type
    if (type === "spectral") model.value.spectralCubes = [];
    else model.value.elementalCubes = [];
  } else {
    const otherArrayLength = type === "spectral" 
      ? model.value.elementalCubes.length 
      : model.value.spectralCubes.length;

    // Minimum cubes based on UploadingPartialData
    const minCubes = UploadingPartialData.value === 'partial' ? 2 : 1;

    // Target length = max of other array length or minimum
    const targetLength = Math.max(otherArrayLength, minCubes);

    const arrayToFill = type === "spectral" ? model.value.spectralCubes : model.value.elementalCubes;

    while (arrayToFill.length < targetLength) {
      addElementToWorkspace(type === "spectral" ? "spectral_cube" : "elemental_cube");
    }
  }
}

// Call the handle function when the value of the checkbox changes
watch(includeSpectral, (newVal) => {
  handleIncludeChange('spectral', newVal)
})

watch(includeElemental, (newVal) => {
  handleIncludeChange('elemental', newVal)
})


/**
 * Adds a component of the type specified by addElementType to the workspace model.
 */
function addElementToWorkspace(type: string) {
  const elementType = type;

  switch (elementType) {
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
 * Removes a specified element from the model by index.
 * @param type - The type of the element to remove.
 * @param index - The index of the element to remove.
 */
function removeElement(type: string, index: number) {
  switch (type) {
    case "contextual_image":
      model.value.contextualImages.splice(index, 1);
      break;
    case "spectral_cube":
      model.value.spectralCubes.splice(index, 1);
      break;
    case "elemental_cube":
      model.value.elementalCubes.splice(index, 1);
      break;
  }
}

// Computes the largest number of datacubes currently in the model
const maxCubes = computed(() => {
  const spectralCount = model.value.spectralCubes.length;
  const elementalCount = model.value.elementalCubes.length;
  return Math.max(spectralCount, elementalCount);
});

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
        <div class="col-span-full text-sm font-medium text-gray-500 mb-1 justify-self-start">
          Base image
        </div>
        <Image class="ml-2 size-6" title="Base image" />
        <Input placeholder="Name" v-model:model-value="model.baseImage.name" />
        <FileSetupTableRow type="an image" :options="imageFiles" v-model="model.baseImage.imageLocation" />
        <Separator class="col-span-full" />

        <!-- Paired Spectral & Elemental Datacubes -->
        <template v-for="index in maxCubes" :key="index" v-if="includeElemental || includeSpectral">
          <!-- Section header -->
          <div class="col-span-full font-semibold text-lg mt-4 mb-2 justify-self-start">
            Datacube <span v-if="(model.spectralCubes.length > 1 || model.elementalCubes.length > 1) && (includeElemental || includeSpectral)"> {{ index}}</span>
          </div>
          <!-- Spectral datacube -->
          <div v-if="includeSpectral" class="col-span-full grid grid-cols-subgrid gap-2">
            <div class="col-span-full text-sm font-medium text-gray-500 mb-1 justify-self-start">
              Spectral Datacube
            </div>
            <AudioWaveform class="ml-2 size-6" title="Spectral datacube" />
            <Input placeholder="Name" v-model:model-value="model.spectralCubes[index - 1].name" />
            <FileSetupTableRow type="a raw" :options="rawFiles" v-model="model.spectralCubes[index - 1].rawLocation" />
            <Button
              v-if="(index - 1 > 0 && UploadingPartialData === 'full') || (index - 1 > 1 && UploadingPartialData === 'partial')"
              variant="destructive"
              class="row-span-3 size-full p-2"
              @click="() => { 
                if (includeSpectral) {
                  removeElement('spectral_cube', index - 1);
                } 
                if (includeElemental) {
                  removeElement('elemental_cube', index - 1); 
                }
              }"
            >
              <Trash2 />
            </Button>
            <FileSetupTableRow type="an rpl" :options="rplFiles" v-model="model.spectralCubes[index - 1].rplLocation" />
            <FileSetupTableRow type="a recipe" :options="recipeFiles" v-model="model.spectralCubes[index - 1].recipeLocation" />
          </div>

          <!-- Elemental datacube -->
          <div v-if="includeElemental" class="col-span-full grid grid-cols-subgrid gap-2">
            <div class="col-span-full text-sm font-medium text-gray-500 mb-1 justify-self-start">
              Elemental Datacube
            </div>
            <Atom class="ml-2 size-6" title="Elemental datacube" />
            <Input
              placeholder="Name"
              v-model:model-value="model.elementalCubes[index - 1].name"
            />
            <FileSetupTableRow
              type="a data"
              :options="elementalFiles"
              v-model="model.elementalCubes[index - 1].dataLocation"
            />
            <FileSetupTableRow
              v-if="model.spectralCubes.length === 0"
              type="a recipe"
              :options="recipeFiles"
              v-model="model.elementalCubes[index - 1].recipeLocation"
            />
            <Button
              v-if="(index - 1 > 0 && UploadingPartialData === 'full' && !includeSpectral) || (index - 1 > 1 && UploadingPartialData === 'partial' && !includeSpectral)"
              variant="destructive"
              class="row-span-3 size-full p-2"
              @click="() => { 
                removeElement('spectral_cube', index - 1); 
                removeElement('elemental_cube', index - 1); 
              }"
            >
              <Trash2 />
            </Button>
          </div>
          <Separator class="col-span-full mt-2" />
        </template>
      </div>
    </ScrollArea>

    <Separator class="mb-2" />

    <!-- Footer -->
    <div class="flex justify-between items-start w-full">
      <!-- Toggle + Checkboxes -->
      <div class="flex flex-col space-y-2">
        <!-- Toggle buttons -->
        <ToggleGroup type="single" v-model="UploadingPartialData" class="space-x-2">
          <ToggleGroupItem value="full" variant="outline">
            Full data scan
          </ToggleGroupItem>
          <ToggleGroupItem value="partial" variant="outline">
            Partial data scans
          </ToggleGroupItem>
        </ToggleGroup>

        <!-- Checkboxes -->
        <div class="flex flex-col space-y-2 mt-2">
          <div class="flex items-center space-x-2">
            <Checkbox id="include-spectral" v-model:checked="includeSpectral" />
            <label for="include-spectral" class="text-sm font-medium leading-none">
              Include spectral datacube
            </label>
          </div>

          <div class="flex items-center space-x-2">
            <Checkbox id="include-elemental" v-model:checked="includeElemental" />
            <label for="include-elemental" class="text-sm font-medium leading-none">
              Include elemental datacube
            </label>
          </div>
        </div>
      </div>

      <!-- Add datacube button + Upload dialog -->
      <div class="flex space-x-2 items-center">
        <Button
          v-if="UploadingPartialData === 'partial'"
          variant="outline"
          @click="addDatacube"
        >
          Add partial data cube
        </Button>

        <FileUploadDialog :data-source="model.name" @files-uploaded="fileFetch.execute()" />
      </div>
    </div>
  </div>
</template>
