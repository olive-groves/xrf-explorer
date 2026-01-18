import { WorkspaceConfig } from "@/lib/workspace";
import { useFetch } from "@vueuse/core";
import { computed, ref, onMounted, watch, Ref } from "vue";
import { FrontendConfig } from "@/lib/config";
import { toast } from "vue-sonner";

export const UploadingPartialData = ref<"full" | "partial">("full");
export const includeSpectral = ref(true);
export const includeElemental = ref(true);

export const showDeleteComponentDialog = ref(false);
export const showMultiDeleteDialog = ref(false);
export const showDeleteFileDialog = ref(false);
export const selectedFilesToDelete = ref<string[]>([]);
export const componentNameToDelete = ref<number | null>(null);

const _lastMode = ref<string | null>(null);

/**
 * Filters a list of filenames by their extensions.
 * @param filenames - The filenames to filter.
 * @param extensions - The allowed extensions (without dots).
 * @param empty - Whether to add an empty string to the beginning.
 * @returns The filtered list of filenames.
 */
function filterByExtension(filenames: string[], extensions: string[], empty: boolean = false) {
  const names = filenames.filter((file) => extensions.includes(file.split(".").pop()?.toLowerCase() ?? ""));
  if (empty) names.unshift("");
  return names;
}

/**
 * Main composable for FileSetupTable logic.
 * Manages workspace configuration, file operations, and datacube management.
 * @param model - The reactive workspace configuration model.
 * @param config - The frontend configuration.
 * @returns Object containing computed properties, state, and functions.
 */
export function useFileSetupTable(model: Ref<WorkspaceConfig>, config: FrontendConfig) {
  const fileUrl = computed(() => `${config.api.endpoint}/${model.value.name}/files`);
  const fileFetch = useFetch<string>(fileUrl);
  const files = computed<string[]>(() => JSON.parse(fileFetch.data.value ?? "[]"));
  const imageFiles = computed(() => filterByExtension(files.value, ["tif", "tiff", "png", "jpg", "jpeg", "bmp"]));
  const recipeFiles = computed(() => filterByExtension(files.value, ["csv"]));
  const rawFiles = computed(() => filterByExtension(files.value, ["raw"]));
  const rplFiles = computed(() => filterByExtension(files.value, ["rpl"]));
  const elementalFiles = computed(() => filterByExtension(files.value, ["csv", "dms"]));
  const allProjectFiles = computed(() => (files.value || []).filter((file) => file.toLowerCase() !== "workspace.json"));

  /**
   * Adds a new empty datacube to the workspace.
   * @param type - The type of datacube to add: 'spectral_cube' or 'elemental_cube'.
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
   * Initializes spectral datacube array based on mode and settings.
   * Ensures minimum number of cubes and synchronization with elemental cubes.
   * @param minCubes - Minimum number of cubes to initialize.
   * @param partial - Whether in partial mode.
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
   * Initializes elemental datacube array based on mode and settings.
   * Ensures minimum number of cubes and synchronization with spectral cubes.
   * @param minCubes - Minimum number of cubes to initialize.
   * @param partial - Whether in partial mode.
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

  /**
   * Initializes the workspace stitching mode and clears opposite mode arrays.
   * @param mode - The stitching mode to initialize: 'full' or 'partial'.
   */
  function initMode(mode: string) {
    const partial = mode === "partial";
    UploadingPartialData.value = mode as "full" | "partial";
    model.value.stitchingMode = mode as "full" | "partial";
    _lastMode.value = mode;

    const minCubes = partial ? 2 : 1;

    initModeSpectral(minCubes, partial);
    initModeElemental(minCubes, partial);

    if (partial) {
      model.value.spectralCubes = [];
      model.value.elementalCubes = [];
    } else {
      model.value.partialSpectralCubes = [];
      model.value.partialElementalCubes = [];
    }
  }

  /**
   * Fills an array with placeholder datacubes until reaching target length.
   * @param array - The array to fill.
   * @param type - The datacube type: 'spectral' or 'elemental'.
   * @param targetLength - The desired final length of the array.
   */
  function addPlaceholders(array: unknown[], type: "spectral" | "elemental", targetLength: number) {
    while (array.length < targetLength) {
      addElementToWorkspace(type === "spectral" ? "spectral_cube" : "elemental_cube");
    }
  }

  /**
   * Handles enabling or disabling a datacube type.
   * Updates the array to match the other datacube type's length.
   * @param type - The datacube type: 'spectral' or 'elemental'.
   * @param value - Whether the type is enabled.
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

    if (!value) {
      array.splice(0);
      return;
    }

    const minCubes = partial ? 2 : 1;
    const otherArray =
      type === "spectral"
        ? partial
          ? model.value.partialElementalCubes
          : model.value.elementalCubes
        : partial
          ? model.value.partialSpectralCubes
          : model.value.spectralCubes;

    const targetLength = Math.max(minCubes, otherArray.length);
    addPlaceholders(array, type, targetLength);
  }

  /**
   * Adds a new full datacube pair (spectral and elemental if enabled).
   */
  function addDatacube() {
    if (includeSpectral.value) addElementToWorkspace("spectral_cube");
    if (includeElemental.value) addElementToWorkspace("elemental_cube");
  }

  /**
   * Determines if a datacube fragment can be deleted.
   * Full mode requires at least 2 fragments, partial mode requires at least 3.
   * @param index - The fragment index (1-based).
   * @returns True if the fragment can be deleted.
   */
  function canDeleteFragment(index: number) {
    return UploadingPartialData.value === "full" ? index > 1 : index > 2;
  }

  /**
   * Removes a datacube fragment from the workspace and syncs with backend.
   * @param fragmentIndex - The index of the fragment to remove (1-based).
   */
  async function removeComponentsFromWorkspace(fragmentIndex: number | null) {
    if (fragmentIndex === null) return;

    const partial = UploadingPartialData.value === "partial";
    const spectralList = partial ? model.value.partialSpectralCubes : model.value.spectralCubes;
    const elementalList = partial ? model.value.partialElementalCubes : model.value.elementalCubes;

    const specIndex = spectralList.length >= fragmentIndex ? fragmentIndex - 1 : null;
    const elemIndex = elementalList.length >= fragmentIndex ? fragmentIndex - 1 : null;

    if (specIndex !== null && spectralList[specIndex]) spectralList.splice(specIndex, 1);
    if (elemIndex !== null && elementalList[elemIndex]) elementalList.splice(elemIndex, 1);

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
   * Adds a new contextual image to the workspace.
   */
  function addContextualImage() {
    model.value.contextualImages.push({
      name: "",
      imageLocation: "",
      recipeLocation: "",
    });
  }

  /**
   * Removes a contextual image from the workspace.
   * @param index - The index of the image to remove.
   */
  function removeContextualImage(index: number) {
    model.value.contextualImages.splice(index, 1);
  }

  /**
   * Removes a file reference from all workspace components.
   * Clears the file from any location it's referenced in.
   * @param filename - The name of the file to remove.
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
   * Deletes multiple files from the backend and updates workspace references.
   * Sends deletion request and removes all references to deleted files.
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

      toast.info("Deleted " + result.deleted.length + " files");
    } catch (error) {
      console.error("Error during multi-delete:", error);
    }

    selectedFilesToDelete.value = [];
    showMultiDeleteDialog.value = false;
    showDeleteFileDialog.value = false;
  }

  /**
   * Fetches the current list of files from the backend.
   */
  async function fetchFiles() {
    console.log("Fetching files...");
    await fileFetch.execute();
  }

  const spectralArr = computed(() =>
    UploadingPartialData.value === "partial" ? model.value.partialSpectralCubes : model.value.spectralCubes,
  );
  const elementalArr = computed(() =>
    UploadingPartialData.value === "partial" ? model.value.partialElementalCubes : model.value.elementalCubes,
  );
  const maxCubes = computed(() => Math.max(spectralArr.value.length, elementalArr.value.length));

  onMounted(() => {
    let startMode: "full" | "partial" = "full";

    if (model.value.spectralCubes.length > 0 || model.value.elementalCubes.length > 0) {
      startMode = "full";
    } else if (model.value.partialSpectralCubes.length > 0 || model.value.partialElementalCubes.length > 0) {
      startMode = "partial";
    }

    UploadingPartialData.value = startMode;
    initMode(startMode);
  });

  watch(UploadingPartialData, (val) => {
    if (val !== _lastMode.value) initMode(val);
  });
  watch(includeSpectral, (val) => handleIncludeChange("spectral", val));
  watch(includeElemental, (val) => handleIncludeChange("elemental", val));
  watch(showDeleteFileDialog, async (newVal) => {
    if (!newVal) {
      await fetchFiles();
    }
  });

  return {
    fileFetch,
    imageFiles,
    recipeFiles,
    rawFiles,
    rplFiles,
    elementalFiles,
    allProjectFiles,
    spectralArr,
    elementalArr,
    maxCubes,
    addDatacube,
    canDeleteFragment,
    removeComponentsFromWorkspace,
    addContextualImage,
    removeContextualImage,
    handleMultiDeleteConfirmed,
  };
}
