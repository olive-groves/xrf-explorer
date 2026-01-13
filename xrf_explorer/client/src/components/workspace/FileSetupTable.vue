<script setup lang="ts">
import { FileSetupTableRow, FileUploadDialog } from ".";
import { WorkspaceConfig } from "@/lib/workspace";
import { useFetch } from "@vueuse/core";
import { computed, inject, ref, onMounted, watch } from "vue";
import { Image, AudioWaveform, Atom, Trash2 } from "lucide-vue-next";
import { FrontendConfig } from "@/lib/config";
import { ScrollArea } from "../ui/scroll-area";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";

const config = inject<FrontendConfig>("config")!;
const model = defineModel<WorkspaceConfig>({ required: true });

// Stitching & workspace flags
const UploadingPartialData = ref("full");
const includeSpectral = ref(true);
const includeElemental = ref(true);

// File fetching
const fileUrl = computed(() => `${config.api.endpoint}/${model.value.name}/files`);
const fileFetch = useFetch<string>(fileUrl);
const files = computed<string[]>(() => JSON.parse(fileFetch.data.value ?? "[]"));
const imageFiles = computed(() => filterByExtension(files.value, ["tif", "tiff", "png", "jpg", "jpeg", "bmp"]));
const recipeFiles = computed(() => filterByExtension(files.value, ["csv"]));
const rawFiles = computed(() => filterByExtension(files.value, ["raw"]));
const rplFiles = computed(() => filterByExtension(files.value, ["rpl"]));
const elementalFiles = computed(() => filterByExtension(files.value, ["csv", "dms"]));

// Deletion state
const showDeleteComponentDialog = ref(false);
const showMultiDeleteDialog = ref(false);
const showDeleteFileDialog = ref(false);
const selectedFilesToDelete = ref<string[]>([]);
const componentNameToDelete = ref<number | null>(null);
const allProjectFiles = computed(() => (files.value || []).filter((file) => file.toLowerCase() !== "workspace.json"));

// Last stitching mode
const _lastMode = ref<string | null>(null);

/**
 * Initialize the workspace stitching mode.
 * @param mode What mode to initialize: full | partial.
 */
function initMode(mode: string) {
  const partial = mode === "partial";
  UploadingPartialData.value = mode as "full" | "partial";
  model.value.stitchingMode = mode as "full" | "partial";
  _lastMode.value = mode;

  const minCubes = partial ? 2 : 1;

  // --- Spectral ---
  if (includeSpectral.value) {
    const targetLength = Math.max(
      minCubes,
      includeElemental.value ? (partial ? model.value.partialElementalCubes.length : model.value.elementalCubes.length) : minCubes
    );
    const array = partial ? model.value.partialSpectralCubes : model.value.spectralCubes;
    while (array.length < targetLength) addElementToWorkspace("spectral_cube");
  } else {
    (partial ? model.value.partialSpectralCubes : model.value.spectralCubes).splice(0);
  }

  // --- Elemental ---
  if (includeElemental.value) {
    const targetLength = Math.max(
      minCubes,
      includeSpectral.value ? (partial ? model.value.partialSpectralCubes.length : model.value.spectralCubes.length) : minCubes
    );
    const array = partial ? model.value.partialElementalCubes : model.value.elementalCubes;
    while (array.length < targetLength) addElementToWorkspace("elemental_cube");
  } else {
    (partial ? model.value.partialElementalCubes : model.value.elementalCubes).splice(0);
  }

  // Clear opposite mode arrays
  if (partial) {
    model.value.spectralCubes = [];
    model.value.elementalCubes = [];
  } else {
    model.value.partialSpectralCubes = [];
    model.value.partialElementalCubes = [];
  }
}

onMounted(() => {
  let startMode: "full" | "partial" = "full";

  // Decide initial mode based on what cubes exist
  if (model.value.partialSpectralCubes.length > 0 || model.value.partialElementalCubes.length > 0) {
    startMode = "partial";
  } else if (model.value.spectralCubes.length > 0 || model.value.elementalCubes.length > 0) {
    startMode = "full";
  }

  UploadingPartialData.value = startMode;
  initMode(startMode);
});

/**
 * Filters a list of filenames on which file extensions are allowed.
 * @param filenames The filenames to filter.
 * @param extensions The extensions to filter on.
 * @param empty Whether to add an empty string.
 * @returns The filtered list of filenames.
 */
function filterByExtension(filenames: string[], extensions: string[], empty: boolean = false) {
  const names = filenames.filter((file) => extensions.includes(file.split(".").pop()?.toLowerCase() ?? ""));
  if (empty) names.unshift("");
  return names;
}

// Watchers
watch(UploadingPartialData, (val) => {
  if (val !== _lastMode.value) initMode(val);
});
watch(includeSpectral, (val) => handleIncludeChange("spectral", val));
watch(includeElemental, (val) => handleIncludeChange("elemental", val));

/**
 * Add a new datacube to the workspace.
 */
function addDatacube() {
  if (includeSpectral.value) addElementToWorkspace("spectral_cube");
  if (includeElemental.value) addElementToWorkspace("elemental_cube");
}

/**
 * Handles enabling or disabling a datacube type.
 * @param type The type of the datacube: spectral | elemental.
 * @param value Whether the datacube type is enabled.
 */
function handleIncludeChange(type: "spectral" | "elemental", value: boolean) {
  const partial = UploadingPartialData.value === "partial";
  const array = type === "spectral" ? (partial ? model.value.partialSpectralCubes : model.value.spectralCubes)
                                   : (partial ? model.value.partialElementalCubes : model.value.elementalCubes);

  // Remove if deselected
  if (!value) {
    array.splice(0);
    return;
  }

  // Determine min placeholders
  const minCubes = partial ? 2 : 1;

  // Determine target length based on the other type
  const otherArray = type === "spectral"
    ? (partial ? model.value.partialElementalCubes : model.value.elementalCubes)
    : (partial ? model.value.partialSpectralCubes : model.value.spectralCubes);

  const targetLength = Math.max(minCubes, otherArray.length);

  // Add placeholders to reach target length
  while (array.length < targetLength) {
    addElementToWorkspace(type === "spectral" ? "spectral_cube" : "elemental_cube");
  }
}


/**
 * Add a new empty datacube to the workspace.
 * @param type The type of datacube to add.
 */
function addElementToWorkspace(type: string) {
  const partial = UploadingPartialData.value === "partial";
  if (type === "spectral_cube")
    (partial ? model.value.partialSpectralCubes : model.value.spectralCubes).push({
      name: "",
      rawLocation: "",
      rplLocation: "",
      recipeLocation: "",
    });
  else
    (partial ? model.value.partialElementalCubes : model.value.elementalCubes).push({
      name: "",
      dataLocation: "",
      recipeLocation: "",
    });
}

/**
 * Determine if a datacube fragment can be deleted.
 * @param index The index of the fragment.
 * @returns Whether the fragment can be deleted or not.
 */
function canDeleteFragment(index: number) {
  if (UploadingPartialData.value === "full") {
    // In full mode, fragment 1 cannot be deleted
    return index > 1;
  } else {
    // In partial mode, first 2 fragments cannot be deleted
    return index > 2;
  }
}

/**
 * Removes a fragment from the workspace.
 * @param fragmentIndex The index of the fragment to remove.
 */
async function removeComponentsFromWorkspace(fragmentIndex: number | null) {
  if (fragmentIndex === null) return;

  const partial = UploadingPartialData.value === "partial";
  const spectralList = partial ? model.value.partialSpectralCubes : model.value.spectralCubes;
  const elementalList = partial ? model.value.partialElementalCubes : model.value.elementalCubes;

  // Compute real indices
  const specIndex = spectralList.length >= fragmentIndex ? fragmentIndex - 1 : null;
  const elemIndex = elementalList.length >= fragmentIndex ? fragmentIndex - 1 : null;

  // Remove spectral if exists
  if (specIndex !== null && spectralList[specIndex]) spectralList.splice(specIndex, 1);

  // Remove elemental if exists
  if (elemIndex !== null && elementalList[elemIndex]) elementalList.splice(elemIndex, 1);

  // Update workspace
  await fileFetch.execute();
  await fetch(`${config.api.endpoint}/${model.value.name}/workspace`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(model.value),
  });

  showDeleteComponentDialog.value = false;
  componentNameToDelete.value = null;
}

/**
 * Removes a file from the workspace.
 * @param filename The name of the file to be removed.
 */
async function removeFileFromComponent(filename: string) {
  console.log("Deleting file from component: " + filename);
  if (model.value.baseImage.name === filename) model.value.baseImage.name = "";

  model.value.contextualImages = model.value.contextualImages.map((img) => ({
    ...img,
    imageLocation: img.imageLocation === filename ? "" : img.imageLocation,
    recipeLocation: img.recipeLocation === filename ? "" : img.recipeLocation,
  }));

  model.value.spectralCubes = model.value.spectralCubes.map((img) => ({
    ...img,
    rawLocation: img.rawLocation === filename ? "" : img.rawLocation,
    recipeLocation: img.recipeLocation === filename ? "" : img.recipeLocation,
    rplLocation: img.rplLocation === filename ? "" : img.rplLocation,
  }));

  model.value.partialSpectralCubes = model.value.partialSpectralCubes.map((img) => ({
    ...img,
    rawLocation: img.rawLocation === filename ? "" : img.rawLocation,
    recipeLocation: img.recipeLocation === filename ? "" : img.recipeLocation,
    rplLocation: img.rplLocation === filename ? "" : img.rplLocation,
  }));

  model.value.elementalCubes = model.value.elementalCubes.map((img) => ({
    ...img,
    dataLocation: img.dataLocation === filename ? "" : img.dataLocation,
    recipeLocation: img.recipeLocation === filename ? "" : img.recipeLocation,
  }));

  model.value.partialElementalCubes = model.value.partialElementalCubes.map((img) => ({
    ...img,
    dataLocation: img.dataLocation === filename ? "" : img.dataLocation,
    recipeLocation: img.recipeLocation === filename ? "" : img.recipeLocation,
  }));

  console.log(model.value);
}

/**
 * Removes multiple files.
 */
async function handleMultiDeleteConfirmed() {
  try {
    const response = await fetch(`${config.api.endpoint}/${model.value.name}/delete_files`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filenames: selectedFilesToDelete.value }),
    });

    if (!response.ok) {
      console.error("Failed to delete files");
      return;
    }

    const result = await response.json();
    for (const filename of result.deleted) {
      void removeFileFromComponent(filename);
    }
  } catch (error) {
    console.error("Error during multi-delete:", error);
  }

  selectedFilesToDelete.value = [];
  showMultiDeleteDialog.value = false;
  showDeleteFileDialog.value = false;
}

// Watcher to refresh files after deletion
watch(showDeleteFileDialog, async (newVal) => {
  if (!newVal) {
    await fetchFiles();
  }
});

/**
 * Fetch the files from the backend.
 */
async function fetchFiles() {
  console.log("Fetching files...");
  await fileFetch.execute();
}

// Computed arrays for stitching layout
const spectralArr = computed(() =>
  UploadingPartialData.value === "partial" ? model.value.partialSpectralCubes : model.value.spectralCubes,
);
const elementalArr = computed(() =>
  UploadingPartialData.value === "partial" ? model.value.partialElementalCubes : model.value.elementalCubes,
);
const maxCubes = computed(() => Math.max(spectralArr.value.length, elementalArr.value.length));

defineExpose({ getUploadingPartialData: () => UploadingPartialData.value });
</script>

<template>
  <div>
    <!-- Header -->
    <div class="grid grid-cols-[2rem,12rem,1fr,2rem] place-items-center gap-2">
      <div class="col-start-2 place-self-start">Name</div>
      <div class="col-start-3 place-self-start">Files</div>
    </div>
    <Separator class="mt-2" />

    <!-- Scroll area -->
    <ScrollArea class="mr-[-0.8125rem] h-[32rem] pr-[0.8125rem]">
      <div class="grid grid-cols-[2rem,12rem,1fr,2rem] place-items-center gap-2 pt-2">
        <!-- Base image -->
        <div class="col-span-full mb-1 justify-self-start text-sm font-medium text-gray-500">Base image</div>
        <Image class="ml-2 size-6" title="Base image" />
        <Input placeholder="Name" v-model:model-value="model.baseImage.name" />
        <FileSetupTableRow type="an image" :options="imageFiles" v-model="model.baseImage.imageLocation" />
        <Separator class="col-span-full" />

        <!-- Fragments -->
        <template v-for="index in maxCubes" :key="index">
          <template v-if="includeElemental || includeSpectral">
            <div class="col-span-full mb-2 mt-4 justify-self-start text-lg font-semibold">Fragment {{ index }}</div>

            <!-- Spectral -->
            <div v-if="includeSpectral && spectralArr[index - 1]" class="col-span-full grid grid-cols-subgrid gap-2">
              <div class="col-span-full mb-1 text-sm font-medium text-gray-500">Spectral Datacube</div>
              <AudioWaveform class="ml-2 size-6" />
              <Input placeholder="Name" v-model:model-value="spectralArr[index - 1].name" />
              <FileSetupTableRow type="a raw" :options="rawFiles" v-model="spectralArr[index - 1].rawLocation" />
              <FileSetupTableRow
                type="an rpl"
                :options="rplFiles"
                v-model="spectralArr[index - 1].rplLocation"
              />
              <FileSetupTableRow
                v-if="UploadingPartialData === 'full'"
                type="a recipe"
                :options="recipeFiles"
                v-model="spectralArr[index - 1].recipeLocation"
              />
            </div>

            <!-- Elemental -->
            <div v-if="includeElemental && elementalArr[index - 1]" class="col-span-full grid grid-cols-subgrid gap-2">
              <div class="col-span-full mb-1 text-sm font-medium text-gray-500">Elemental Datacube</div>
              <Atom class="ml-2 size-6" />
              <Input placeholder="Name" v-model:model-value="elementalArr[index - 1].name" />
              <FileSetupTableRow
                type="a data"
                :options="elementalFiles"
                v-model="elementalArr[index - 1].dataLocation"
              />
              <FileSetupTableRow
                v-if="UploadingPartialData === 'full'"
                type="a recipe"
                :options="recipeFiles"
                v-model="elementalArr[index - 1].recipeLocation"
              />
            </div>

            <!-- Fragment delete button -->
            <Button
              v-if="(spectralArr[index - 1] || elementalArr[index - 1]) && canDeleteFragment(index)"
              variant="destructive"
              class="col-span-full my-2"
              @click="
                componentNameToDelete = index;
                showDeleteComponentDialog = true;
              "
            >
              <Trash2 /> Delete Fragment
            </Button>

            <Separator class="col-span-full mt-2" />
          </template>
        </template>

        <!-- Delete component dialog -->
        <div v-if="showDeleteComponentDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div class="min-w-[320px] rounded-lg bg-background p-6 text-foreground shadow-lg">
            <div class="mb-2 text-lg font-bold">Confirm Deletion</div>
            <div class="mb-4 text-sm text-muted-foreground">
              Are you sure you want to delete this component from the workspace? This action cannot be undone.
            </div>
            <div class="flex justify-end space-x-2">
              <Button variant="outline" @click="showDeleteComponentDialog = false">Cancel</Button>
              <Button variant="destructive" @click="removeComponentsFromWorkspace(componentNameToDelete)"
                >Delete</Button
              >
            </div>
          </div>
        </div>
      </div>
    </ScrollArea>

    <!-- Footer -->
    <div class="mt-2 flex w-full items-start justify-between">
      <div class="flex flex-col space-y-2">
        <ToggleGroup type="single" v-model="UploadingPartialData" class="space-x-2">
          <ToggleGroupItem value="full" variant="outline">Full data scan</ToggleGroupItem>
          <ToggleGroupItem value="partial" variant="outline">Partial data scans</ToggleGroupItem>
        </ToggleGroup>

        <div class="mt-2 flex flex-col space-y-2">
          <div class="flex items-center space-x-2">
            <Checkbox id="include-spectral" v-model:checked="includeSpectral" />
            <label for="include-spectral" class="text-sm font-medium leading-none">Include spectral datacube</label>
          </div>
          <div class="flex items-center space-x-2">
            <Checkbox id="include-elemental" v-model:checked="includeElemental" />
            <label for="include-elemental" class="text-sm font-medium leading-none">Include elemental datacube</label>
          </div>
        </div>
      </div>

      <div class="flex items-center space-x-2">
        <Button v-if="UploadingPartialData === 'partial'" variant="outline" @click="addDatacube"
          >Add partial data cube</Button
        >
        <FileUploadDialog :data-source="model.name" @files-uploaded="fileFetch.execute()" />
        <Button variant="destructive" @click="showMultiDeleteDialog = true"> Delete Files </Button>
      </div>
    </div>

    <!-- Multi-delete dialog -->
    <div v-if="showMultiDeleteDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div class="max-h-[500px] min-w-[360px] overflow-y-auto rounded-lg bg-background p-6 shadow-lg">
        <div class="mb-2 text-lg font-bold">Delete Files</div>
        <div class="mb-4 text-sm">Select the files you want to delete from this project.</div>
        <div class="mb-4 space-y-2">
          <label v-for="file in allProjectFiles" :key="file" class="flex items-center space-x-2">
            <input type="checkbox" :value="file" v-model="selectedFilesToDelete" class="" />
            <span class="truncate">{{ file }}</span>
          </label>
        </div>
        <div class="flex justify-end space-x-2">
          <Button variant="outline" @click="showMultiDeleteDialog = false">Cancel</Button>
          <Button
            variant="destructive"
            :disabled="selectedFilesToDelete.length === 0"
            @click="showDeleteFileDialog = true"
            >Delete Selected</Button
          >
        </div>
      </div>
    </div>

    <!-- Delete files confirmation -->
    <div v-if="showDeleteFileDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div class="min-w-[320px] rounded-lg bg-background p-6 shadow-lg">
        <div class="mb-2 text-lg font-bold">Confirm Deletion</div>
        <div class="mb-4 text-sm">Are you sure you want to delete these files? This action cannot be undone.</div>
        <div class="flex justify-end space-x-2">
          <Button variant="outline" @click="showDeleteFileDialog = false">Cancel</Button>
          <Button variant="destructive" @click="handleMultiDeleteConfirmed">Delete</Button>
        </div>
      </div>
    </div>
  </div>
</template>
