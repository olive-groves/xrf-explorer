import { ContextualImage, WorkspaceConfig } from "@/lib/workspace";
import { createLayer, layerGroups, layers, updateLayerGroupLayers } from "./state";
import { computed, watch } from "vue";
import { appState } from "@/lib/app_state";
import { snakeCase } from "change-case";
import { disposeLayer } from "./scene";
import { LayerGroup, LayerVisibility } from "./types";

const useWorkspace = computed(() => appState.workspace);
watch(useWorkspace, (value) => loadWorkspace(value!), { deep: true });

/**
 * Updates the layers and layergroups when changes are made to the workspaceconfig.
 * @param workspace - The new workspace configuration.
 */
function loadWorkspace(workspace: WorkspaceConfig) {
  // Unload existing workspace
  console.info("Unloading existing workspace from layer system...");
  layerGroups.value = {};
  layers.value.forEach(disposeLayer);
  layers.value = [];

  console.info("Loading new workspace into layer system...");

  // Create base image layer
  createBaseLayer(workspace.baseImage);

  // Create other contextual image layers
  workspace.contextualImages.forEach((image) => {
    createContextualLayer(image);
  });

  // Create elemental layers
  // Create color segmentation layers
  // Create dimensionality reduction layers
}

/**
 * Creates a layer for the base image in the image viewer.
 * @param image - The image to use as the base image.
 */
function createBaseLayer(image: ContextualImage) {
  const layer = createLayer(`base_${snakeCase(image.name)}`, image);

  layerGroups.value.base = {
    type: "base",
    name: image.name,
    description: "Base image",
    layers: [layer],
    index: 1,
    visible: true,
    visibility: LayerVisibility.Visible,
    opacity: [1.0],
    contrast: [1.0],
    saturation: [1.0],
    gamma: [1.0],
  };

  updateLayerGroupLayers(layerGroups.value.base, "initialProperty");
}

/**
 * Creates a layer for a contextual image in the image viewer.
 * @param image - The image to use as the contextual image.
 */
function createContextualLayer(image: ContextualImage) {
  const id = `contextual_${snakeCase(image.name)}`;
  const layer = createLayer(id, image);

  const layerGroup: LayerGroup = {
    type: "contextual",
    name: image.name,
    description: "Contextual image",
    layers: [layer],
    index: 0,
    visible: false,
    visibility: LayerVisibility.Visible,
    opacity: [1.0],
    contrast: [1.0],
    saturation: [1.0],
    gamma: [1.0],
  };

  layerGroups.value[id] = layerGroup;
  updateLayerGroupLayers(layerGroup, "initialProperty");
}
