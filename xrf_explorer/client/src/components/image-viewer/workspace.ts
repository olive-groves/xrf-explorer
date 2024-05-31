import { ContextualImage, WorkspaceConfig } from "@/lib/workspace";
import { createLayer, layerGroups, layers, updateLayerGroupLayers } from "./state";
import { computed, watch } from "vue";
import { appState } from "@/lib/appState";
import { snakeCase } from "change-case";
import { disposeLayer } from "./scene";
import { LayerGroup, LayerVisibility } from "./types";
import { createElementalLayers } from "./elementalHelper";
import { createColorClusterLayers } from "./colorClusterHelper";

const useWorkspace = computed(() => appState.workspace);
watch(useWorkspace, (value) => loadWorkspace(value!), { deep: true });

/**
 * Updates the layers and layergroups when changes are made to the workspaceconfig.
 * @param workspace - The new workspace configuration.
 */
function loadWorkspace(workspace: WorkspaceConfig) {
  // Unload existing workspace
  console.info("Unloading existing workspace from layer system");
  layerGroups.value = {};
  layers.value.forEach(disposeLayer);
  layers.value = [];

  console.info("Loading new workspace into layer system");

  // Create base image layer
  createBaseLayer(workspace.baseImage);

  // Create other contextual image layers
  workspace.contextualImages.forEach((image) => {
    createContextualLayer(image);
  });

  // Create elemental layers
  createElementalLayers(workspace);

  // Create color segmentation layers
  createColorClusterLayers();

  // Create dimensionality reduction layers
}

/**
 * Creates a layer for the base image in the image viewer.
 * @param image - The image to use as the base image.
 */
function createBaseLayer(image: ContextualImage) {
  const layer = createLayer(`base_${snakeCase(image.name)}`, image);

  layerGroups.value.base = {
    name: image.name,
    description: "Base image",
    layers: [layer],
    index: 0,
    visible: true,
    ...layerGroupDefaults,
  };

  updateLayerGroupLayers(layerGroups.value.base);
}

/**
 * Creates a layer for a contextual image in the image viewer.
 * @param image - The image to use as the contextual image.
 */
function createContextualLayer(image: ContextualImage) {
  const id = `contextual_${snakeCase(image.name)}`;
  const layer = createLayer(id, image);

  const layerGroup: LayerGroup = {
    name: image.name,
    description: "Contextual image",
    layers: [layer],
    index: -1,
    visible: false,
    ...layerGroupDefaults,
  };

  layerGroups.value[id] = layerGroup;
  updateLayerGroupLayers(layerGroup);
}

export const layerGroupDefaults = {
  visibility: LayerVisibility.InsideLens,
  opacity: [1.0],
  contrast: [1.0],
  saturation: [1.0],
  gamma: [1.0],
  brightness: [0.0],
};
