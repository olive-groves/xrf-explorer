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
// keep track of last initialized mode to avoid double-init
const _lastMode = ref<string | null>(null);

function initMode(mode: string) {
  // Ensure arrays exist (older workspace.json may not have partial arrays)
  if (!Array.isArray(model.value.spectralCubes)) model.value.spectralCubes = [];
  if (!Array.isArray(model.value.partialSpectralCubes)) model.value.partialSpectralCubes = [];
  if (!Array.isArray(model.value.elementalCubes)) model.value.elementalCubes = [];
  if (!Array.isArray(model.value.partialElementalCubes)) model.value.partialElementalCubes = [];

  if (mode === 'partial') {
    // normalize partial arrays to exactly 2 elements when included
    if (includeSpectral.value) {
      model.value.partialSpectralCubes = model.value.partialSpectralCubes.slice(0, 2);
      while (model.value.partialSpectralCubes.length < 2) {
        model.value.partialSpectralCubes.push({ name: "", rawLocation: "", rplLocation: "", recipeLocation: "" });
      }
    } else {
      model.value.partialSpectralCubes = [];
    }
    if (includeElemental.value) {
      model.value.partialElementalCubes = model.value.partialElementalCubes.slice(0, 2);
      while (model.value.partialElementalCubes.length < 2) {
        model.value.partialElementalCubes.push({ name: "", dataLocation: "", recipeLocation: "" });
      }
    } else {
      model.value.partialElementalCubes = [];
    }
    // clear full arrays
    model.value.spectralCubes = [];
    model.value.elementalCubes = [];
    model.value.stitchingMode = "partial";
  } else {
    // normalize full arrays to exactly 1 element when included
    if (includeSpectral.value) {
      model.value.spectralCubes = model.value.spectralCubes.slice(0, 1);
      if (model.value.spectralCubes.length === 0) model.value.spectralCubes.push({ name: "", rawLocation: "", rplLocation: "", recipeLocation: "" });
    } else {
      model.value.spectralCubes = [];
    }
    if (includeElemental.value) {
      model.value.elementalCubes = model.value.elementalCubes.slice(0, 1);
      if (model.value.elementalCubes.length === 0) model.value.elementalCubes.push({ name: "", dataLocation: "", recipeLocation: "" });
    } else {
      model.value.elementalCubes = [];
    }
    // clear partial arrays
    model.value.partialSpectralCubes = [];
    model.value.partialElementalCubes = [];
    model.value.stitchingMode = "full";
  }

  _lastMode.value = mode;
}

onMounted(() => {
  const startMode = model.value.stitchingMode ?? UploadingPartialData.value ?? 'full';
  UploadingPartialData.value = startMode;
  initMode(startMode);
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
  // Avoid re-initializing if the mode is unchanged
  if (val === _lastMode.value) return;
  initMode(val);
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
    // Remove all cubes of that type from the active arrays
    if (type === "spectral") {
      if (UploadingPartialData.value === 'partial') model.value.partialSpectralCubes = [];
      else model.value.spectralCubes = [];
    } else {
      if (UploadingPartialData.value === 'partial') model.value.partialElementalCubes = [];
      else model.value.elementalCubes = [];
    }
    return;
  }

  // Compute other array length for target sizing (keep parity between arrays in the active mode)
  const otherArrayLength = type === "spectral"
    ? (UploadingPartialData.value === 'partial' ? model.value.partialElementalCubes.length : model.value.elementalCubes.length)
    : (UploadingPartialData.value === 'partial' ? model.value.partialSpectralCubes.length : model.value.spectralCubes.length);

  const minCubes = UploadingPartialData.value === 'partial' ? 2 : 1;
  const targetLength = Math.max(otherArrayLength, minCubes);

  const arrayToFill = type === "spectral"
    ? (UploadingPartialData.value === 'partial' ? model.value.partialSpectralCubes : model.value.spectralCubes)
    : (UploadingPartialData.value === 'partial' ? model.value.partialElementalCubes : model.value.elementalCubes);

  while (arrayToFill.length < targetLength) {
    addElementToWorkspace(type === "spectral" ? "spectral_cube" : "elemental_cube");
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
  const partial = UploadingPartialData.value === 'partial';

  switch (elementType) {
    // Add a new spectral datacube
    case "spectral_cube": {
      if (partial) {
        model.value.partialSpectralCubes.push({ name: "", rawLocation: "", rplLocation: "", recipeLocation: "" });
      } else {
        model.value.spectralCubes.push({ name: "", rawLocation: "", rplLocation: "", recipeLocation: "" });
      }
      break;
    }
    // Add a new elemental datacube
    case "elemental_cube": {
      if (partial) {
        model.value.partialElementalCubes.push({ name: "", dataLocation: "", recipeLocation: "" });
      } else {
        model.value.elementalCubes.push({ name: "", dataLocation: "", recipeLocation: "" });
      }
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
      if (UploadingPartialData.value === 'partial') model.value.partialSpectralCubes.splice(index, 1);
      else model.value.spectralCubes.splice(index, 1);
      break;
    case "elemental_cube":
      if (UploadingPartialData.value === 'partial') model.value.partialElementalCubes.splice(index, 1);
      else model.value.elementalCubes.splice(index, 1);
      break;
  }
}

// Active arrays depending on mode
const spectralArr = computed(() => (UploadingPartialData.value === 'partial' ? model.value.partialSpectralCubes : model.value.spectralCubes));
const elementalArr = computed(() => (UploadingPartialData.value === 'partial' ? model.value.partialElementalCubes : model.value.elementalCubes));

const maxCubes = computed(() => {
  const spectralCount = spectralArr.value.length;
  const elementalCount = elementalArr.value.length;
  return Math.max(spectralCount, elementalCount);
});

// Small accessor so parent dialogs can read the current UploadingPartialData
// and save stitchingMode when the Save button is pressed.
defineExpose({
  getUploadingPartialData: () => UploadingPartialData.value,
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
            Datacube <span v-if="(spectralArr.length > 1 || elementalArr.length > 1) && (includeElemental || includeSpectral)"> {{ index}}</span>
          </div>
          <!-- Spectral datacube -->
          <div v-if="includeSpectral" class="col-span-full grid grid-cols-subgrid gap-2">
            <div class="col-span-full text-sm font-medium text-gray-500 mb-1 justify-self-start">
              Spectral Datacube
            </div>
            <AudioWaveform class="ml-2 size-6" title="Spectral datacube" />
            <Input placeholder="Name" v-model:model-value="spectralArr[index - 1].name" />
            <FileSetupTableRow type="a raw" :options="rawFiles" v-model="spectralArr[index - 1].rawLocation" />
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
            <FileSetupTableRow type="an rpl" :options="rplFiles" v-model="spectralArr[index - 1].rplLocation" />
            <FileSetupTableRow type="a recipe" :options="recipeFiles" v-model="spectralArr[index - 1].recipeLocation" />
          </div>

          <!-- Elemental datacube -->
          <div v-if="includeElemental" class="col-span-full grid grid-cols-subgrid gap-2">
            <div class="col-span-full text-sm font-medium text-gray-500 mb-1 justify-self-start">
              Elemental Datacube
            </div>
            <Atom class="ml-2 size-6" title="Elemental datacube" />
            <Input
              placeholder="Name"
              v-model:model-value="elementalArr[index - 1].name"
            />
            <FileSetupTableRow
              type="a data"
              :options="elementalFiles"
              v-model="elementalArr[index - 1].dataLocation"
            />
            <FileSetupTableRow
              v-if="spectralArr.length === 0"
              type="a recipe"
              :options="recipeFiles"
              v-model="elementalArr[index - 1].recipeLocation"
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
