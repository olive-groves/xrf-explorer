// Import necessary modules
import { ContextualImage, WorkspaceConfig } from "@/lib/workspace";
import { createLayer, layerGroups, layers, updateLayerGroupLayers } from "./state";
import { computed, watch } from "vue";
import { appState, datasource } from "@/lib/appState";
import { snakeCase } from "change-case";
import { disposeLayer } from "./scene";
import { LayerGroup, LayerVisibility } from "./types";
import { config } from "@/main";
import { createElementalLayers } from "./elementalHelper";
import { loadPlaceholderLayer } from "./colorClusterHelper";
import { registerLayer } from "./registering";
import { getImageSize, getRecipe, getTargetSize } from "./api";
import { createDRSelectionLayer } from "./drSelectionHelper";

const useWorkspace = computed(() => appState.workspace);
watch(useWorkspace, (value) => loadWorkspace(value!), { deep: true });

/**
 * Updates the layers and layer groups when changes are made to the workspace config.
 * @param workspace - The new workspace configuration.
 */
async function loadWorkspace(workspace: WorkspaceConfig) {
  // Unload existing workspace
  console.info("Unloading existing workspace from layer system");
  layerGroups.value = {};
  await layers.value.forEach(disposeLayer);
  layers.value = [];

  console.info("Loading new workspace into layer system");

  // Create base image layer
  createBaseLayer(workspace.baseImage);

  // Create other contextual image layers
  workspace.contextualImages.forEach(async (image) => {
    await createContextualLayer(image);
  });

  // Return if there is no elemental data as the other visualizations do not work in that case.
  if (workspace.elementalCubes.length == 0) return;

  // Create elemental layers
  await createElementalLayers(workspace);

  // Create color segmentation layers
  await loadPlaceholderLayer();

  // Create selection layers
  await createDRSelectionLayer();
}

/**
 * Creates a layer for the base image in the image viewer.
 * @param image - The image to use as the base image.
 */
function createBaseLayer(image: ContextualImage) {
  const layer = createLayer(`base_${snakeCase(image.name)}`, getContextualImageUrl(image));

  layerGroups.value.base = {
    name: image.name,
    description: "Base image",
    layers: [layer],
    index: 0,
    visible: true,
    default_visibility: true,
    ...layerGroupDefaults,
  };

  updateLayerGroupLayers(layerGroups.value.base);
}

/**
 * Creates a layer for a contextual image in the image viewer.
 * @param image - The image to use as the contextual image.
 */
async function createContextualLayer(image: ContextualImage) {
  const id = `contextual_${snakeCase(image.name)}`;
  const layer = createLayer(id, getContextualImageUrl(image));

  await getRecipe(getContextualImageRecipeUrl(image)).then(async (recipe) => {
    recipe.movingSize = await getImageSize(image.name);
    recipe.targetSize = await getTargetSize();
    registerLayer(layer, recipe);
  });

  const layerGroup: LayerGroup = {
    name: image.name,
    description: "Contextual image",
    layers: [layer],
    index: -1,
    visible: false,
    default_visibility: false,
    ...layerGroupDefaults,
  };

  layerGroups.value[id] = layerGroup;
  updateLayerGroupLayers(layerGroup);
}

/**
 * Gets the url for a specified contextual image.
 * @param image - The contextual image.
 * @returns The url to the image represented by the contextual image.
 */
function getContextualImageUrl(image: ContextualImage): string {
  return `${config.api.endpoint}/${datasource.value}/image/${image.name}`;
}

/**
 * Gets the url for the recipe of a specified contextual image.
 * @param image - The contextual image.
 * @returns The url to the image represented by the contextual image.
 */
function getContextualImageRecipeUrl(image: ContextualImage): string {
  return getContextualImageUrl(image) + "/recipe";
}

/**
 * Default values for some LayerGroup fields.
 */
export const layerGroupDefaults = {
  visibility: LayerVisibility.Visible,
  opacity: [1.0],
  contrast: [1.0],
  saturation: [1.0],
  gamma: [1.0],
  brightness: [0.0],
  pinned: false,
};

/**
 * Builds the URL to an image that lives in the workspace uploads folder.
 * @param imageLocation - Name or relative path of the image in the workspace.
 * @param workspaceName - Optional workspace name. If omitted, uses current datasource.
 * @returns The full URL to the image.
 */
export function getWorkspaceImageUrl(imageLocation: string, workspaceName?: string): string {
  const ds = workspaceName ?? datasource.value;
  const segments = imageLocation.split("/").map((s) => encodeURIComponent(s));
  return `${config.api.endpoint}/${ds}/image/${segments.join("/")}`;
}

/**
 * Builds the URL to a generated partial greyscale image.
 * @param imageLocation - Name or relative path of the greyscale in the workspace.
 * @param workspaceName - Optional workspace name.
 * @returns The full URL to the greyscale image.
 */
export function getWorkspaceGreyscaleUrl(imageLocation: string, workspaceName?: string): string {
  const ds = workspaceName ?? datasource.value;
  return `${config.api.endpoint}/${ds}/stitch_datacubes/greyscale_image/${encodeURIComponent(imageLocation)}`;
}

/**
 * Saves the updated workspace to the backend.
 */
export async function saveWorkspaceToBackend() {
  const ws = appState.workspace;
  if (!ws) return;

  try {
    await fetch(`/api/${ws.name}/workspace`, {
      method: "POST",
      body: JSON.stringify(ws),
      headers: { "Content-Type": "application/json" },
    });
    console.log("Workspace saved");
  } catch (e) {
    console.warn("Failed saving workspace", e);
  }
  return;
}

let saveTimeout: number | null = null;

/**
 * Makes sure we do not spam the back end while mapping.
 */
export function saveWorkspaceDebounced() {
  if (saveTimeout) window.clearTimeout(saveTimeout);

  saveTimeout = window.setTimeout(async () => {
    await saveWorkspaceToBackend();
    saveTimeout = null;
  }, 500);
}
