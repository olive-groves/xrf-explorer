import { ref } from "vue";
import { Layer, LayerGroup, LayerVisibility } from "./types";
import { ContextualImage } from "@/lib/workspace";
import * as THREE from "three";
import { loadLayer } from "./scene";

/**
 * Contains data for all layers.
 * May not be mutated directly from outside of the ImageViewer.
 */
export const layers = ref<Layer[]>([]);

/**
 * Describes the different layer groups.
 * May not be mutated directly from outside of the ImageViewer.
 */
export const layerGroups = ref<{
  [key: string]: LayerGroup;
}>({});

/**
 * Create a layer from an image resource.
 * Handles registering and loading in the image viewer.
 * @param id - The ID to associate with the layer.
 * @param image - The image to load in the layer.
 * @returns The layer that was created by calling the function.
 */
export function createLayer(id: string, image: ContextualImage): Layer {
  console.log("Creating layer", id, image);

  const layer: Layer = {
    id: id,
    url: image.imageLocation,
    uniform: {
      iIndex: { value: 0 },
      iViewport: { value: new THREE.Vector4() },
      mRegister: { value: new THREE.Matrix3() },
      iShowLayer: { value: 0 },
      uOpacity: { value: 0 },
      uMouse: { value: new THREE.Vector2() },
      uRadius: { value: 0 },
    },
  };

  layers.value.push(layer);

  loadLayer(layer);

  return layer;
}

/**
 * Helper function that completely updates the layers in a layer group.
 * @param group - The layer group that should be updated.
 */
export function updateLayerGroupLayers(group: LayerGroup) {
  setLayerGroupIndex(group);
  setLayerGroupVisibility(group);
  setLayerGroupOpacity(group);
}

/**
 * Updates the iIndex uniform for all layers in a layer group.
 * @param group - The layer group that should be updated.
 */
export function setLayerGroupIndex(group: LayerGroup) {
  group.layers.forEach((layer) => (layer.uniform.iIndex.value = group.index));
}

/**
 * Updates the visibility uniforms for all layers in a layer group.
 * @param group - The group that should be updated.
 */
export function setLayerGroupVisibility(group: LayerGroup) {
  const visibility = group.visible ? group.visibility : LayerVisibility.Invisible;

  group.layers.forEach((layer) => (layer.uniform.iShowLayer.value = visibility));
}

/**
 * Updates the opacity uniform for all layers in a layer group.
 * @param group - The group that should be updated.
 */
export function setLayerGroupOpacity(group: LayerGroup) {
  group.layers.forEach((layer) => (layer.uniform.uOpacity.value = group.opacity[0]));
}
