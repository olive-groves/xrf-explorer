import { WorkspaceConfig } from "@/lib/workspace";
import { useFetch } from "@vueuse/core";
import { computed, inject, ref, onMounted, watch } from "vue";
import { FrontendConfig } from "@/lib/config";
import { toast } from "vue-sonner";

const config = inject<FrontendConfig>("config")!;
export const model = defineModel<WorkspaceConfig>({ required: true });

// Stitching & workspace flags
export const UploadingPartialData = ref("full");
export const includeSpectral = ref(true);
export const includeElemental = ref(true);

// File fetching
const fileUrl = computed(() => `${config.api.endpoint}/${model.value.name}/files`);
export const fileFetch = useFetch<string>(fileUrl);
const files = computed<string[]>(() => JSON.parse(fileFetch.data.value ?? "[]"));
const imageFiles = computed(() => filterByExtension(files.value, ["tif", "tiff", "png", "jpg", "jpeg", "bmp"]));
const recipeFiles = computed(() => filterByExtension(files.value, ["csv"]));
const rawFiles = computed(() => filterByExtension(files.value, ["raw"]));
const rplFiles = computed(() => filterByExtension(files.value, ["rpl"]));
const elementalFiles = computed(() => filterByExtension(files.value, ["csv", "dms"]));

/**
 * Function to export file fetching variables.
 * @returns The file fetching variables.
 */
export function exportFileFetchingVariables() {
  return { imageFiles, recipeFiles, rawFiles, rplFiles, elementalFiles };
}

// Deletion state
export const showDeleteComponentDialog = ref(false);
export const showMultiDeleteDialog = ref(false);
export const showDeleteFileDialog = ref(false);
export const selectedFilesToDelete = ref<string[]>([]);
export const componentNameToDelete = ref<number | null>(null);
const allProjectFiles = computed(() => (files.value || []).filter((file) => file.toLowerCase() !== "workspace.json"));

/**
 * Function to export deletion variables.
 * @returns The deletion variables.
 */
export function exportDeletionVariables() {
  return { allProjectFiles };
}

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
  initModeSpectral(minCubes, partial);

  // --- Elemental ---
  initModeElemental(minCubes, partial);

  // Clear opposite mode arrays
  if (partial) {
    model.value.spectralCubes = [];
    model.value.elementalCubes = [];
  } else {
    model.value.partialSpectralCubes = [];
    model.value.partialElementalCubes = [];
  }
}

/**
 * Initialize spectral datacube mode.
 * @param minCubes - Minimum number of cubes to initialize.
 * @param partial - Whether to initialize partial cubes.
 */
function initModeSpectral(minCubes: number, partial: boolean) {
  if (includeSpectral.value) {
    const targetLength = Math.max(
      minCubes,
      includeElemental.value
        ? partial
          ? model.value.partialElementalCubes.length
          : model.value.elementalCubes.length
        : minCubes,
    );
    const array = partial ? model.value.partialSpectralCubes : model.value.spectralCubes;
    while (array.length < targetLength) addElementToWorkspace("spectral_cube");
  } else {
    (partial ? model.value.partialSpectralCubes : model.value.spectralCubes).splice(0);
  }
}

/**
 * Function to initialize elemental datacube mode.
 * @param minCubes - Minimum number of cubes to initialize.
 * @param partial - Whether to initialize partial cubes.
 */
function initModeElemental(minCubes: number, partial: boolean) {
  if (includeElemental.value) {
    const targetLength = Math.max(
      minCubes,
      includeSpectral.value
        ? partial
          ? model.value.partialSpectralCubes.length
          : model.value.spectralCubes.length
        : minCubes,
    );
    const array = partial ? model.value.partialElementalCubes : model.value.elementalCubes;
    while (array.length < targetLength) addElementToWorkspace("elemental_cube");
  } else {
    (partial ? model.value.partialElementalCubes : model.value.elementalCubes).splice(0);
  }
}

onMounted(() => {
  let startMode: "full" | "partial" = "full";

  // Decide initial mode based on what cubes exist
  if (model.value.spectralCubes.length > 0 || model.value.elementalCubes.length > 0) {
    startMode = "full";
  } else if (model.value.partialSpectralCubes.length > 0 || model.value.partialElementalCubes.length > 0) {
    startMode = "partial";
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
 * Add a new full datacube to the workspace.
 */
export function addDatacube() {
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
  const array =
    type === "spectral"
      ? partial
        ? model.value.partialSpectralCubes
        : model.value.spectralCubes
      : partial
        ? model.value.partialElementalCubes
        : model.value.elementalCubes;

  // Remove if deselected
  if (!value) {
    array.splice(0);
    return;
  }

  // Determine min placeholders
  const minCubes = partial ? 2 : 1;

  // Determine target length based on the other type
  const otherArray =
    type === "spectral"
      ? partial
        ? model.value.partialElementalCubes
        : model.value.elementalCubes
      : partial
        ? model.value.partialSpectralCubes
        : model.value.spectralCubes;

  const targetLength = Math.max(minCubes, otherArray.length);

  // Add placeholders to reach target length
  addPlaceholders(array, type, targetLength);
}

/**
 * Fill an array with placeholder datacubes until it reaches the target length.
 * @param array - The array to fill.
 * @param type - The type of datacube: spectral | elemental.
 * @param targetLength - The desired length of the array.
 */
function addPlaceholders(array: unknown[], type: "spectral" | "elemental", targetLength: number) {
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
export function canDeleteFragment(index: number) {
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
export async function removeComponentsFromWorkspace(fragmentIndex: number | null) {
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
 * Adds a contextual image to the workspace.
 */
export function addContextualImage() {
  model.value.contextualImages.push({
    name: "",
    imageLocation: "",
    recipeLocation: "",
  });
}

/**
 * Removes a contextual image from the workspace.
 * @param index - The index of the contaxtual image in the array in the workspace that needs to be removed.
 */
export function removeContextualImage(index: number) {
  model.value.contextualImages.splice(index, 1);
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
export async function handleMultiDeleteConfirmed() {
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

    toast.info("Deleted " + result.deleted.length + " files");
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

/**
 * Computed arrays for stitching layout.
 */
export const spectralArr = computed(() =>
  UploadingPartialData.value === "partial" ? model.value.partialSpectralCubes : model.value.spectralCubes,
);
export const elementalArr = computed(() =>
  UploadingPartialData.value === "partial" ? model.value.partialElementalCubes : model.value.elementalCubes,
);
export const maxCubes = computed(() => Math.max(spectralArr.value.length, elementalArr.value.length));

defineExpose({ getUploadingPartialData: () => UploadingPartialData.value });
