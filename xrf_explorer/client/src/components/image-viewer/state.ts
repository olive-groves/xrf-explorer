import { ref } from "vue";
import { Layer, LayerGroup, LayerType, LayerVisibility } from "./types";
import { ContextualImage } from "@/lib/workspace";
import * as THREE from "three";
import { loadLayer } from "./scene";
import { registerLayer } from "./registering";

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
 * @param load - Whether the layer should be loaded into the image viewer.
 * @returns The layer that was created by calling the function.
 */
export function createLayer(id: string, image: ContextualImage, load: boolean = true): Layer {
  console.info("Creating layer", id, image);

  const layer: Layer = {
    id: id,
    image: image.imageLocation,
    uniform: {
      iIndex: { value: 0 },
      iLayerType: { value: LayerType.Image },
      iViewport: { value: new THREE.Vector4() },
      mRegister: { value: new THREE.Matrix3() },
      iShowLayer: { value: LayerVisibility.Invisible },
      uOpacity: { value: 1 },
      uContrast: { value: 1 },
      uSaturation: { value: 1 },
      uGamma: { value: 1 },
      uBrightness: { value: 0 },
      uMouse: { value: new THREE.Vector2() },
      uRadius: { value: 0 },
    },
  };

  layers.value.push(layer);

  if (load) loadLayer(layer);

  registerLayer(layer, image);

  return layer;
}

/**
 * Helper function that completely updates the layers in a layer group.
 * @param group - The layer group that should be updated.
 */
export function updateLayerGroupLayers(group: LayerGroup) {
  setLayerGroupIndex(group);
  setLayerGroupVisibility(group);
  setLayerGroupProperty(group, "opacityProperty");
  setLayerGroupProperty(group, "contrastProperty");
  setLayerGroupProperty(group, "saturationProperty");
}

/**
 * Updates the iIndex uniform for all layers in a layer group.
 * @param group - The layer group that should be updated.
 */
export function setLayerGroupIndex(group: LayerGroup) {
  group.layers.forEach((layer) => {
    layer.uniform.iIndex.value = group.index;
    if (layer.mesh != undefined) {
      layer.mesh!.renderOrder = -group.index;
    }
  });
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
 * Updates the specified uniform for all layers in a layer group.
 * @param group - The layer group that should be updated.
 * @param property - The property to update (e.g., "opacity", "contrast", "saturation").
 */
export function setLayerGroupProperty(group: LayerGroup, property: string) {
  group.layers.forEach((layer) => {
    switch (property) {
      case "opacityProperty":
        layer.uniform.uOpacity.value = group.opacity[0];
        break;
      case "contrastProperty":
        layer.uniform.uContrast.value = group.contrast[0];
        break;
      case "saturationProperty":
        layer.uniform.uSaturation.value = group.saturation[0];
        break;
      case "gammaProperty":
        layer.uniform.uGamma.value = group.gamma[0];
        break;
      case "brightnessProperty":
        layer.uniform.uBrightness.value = group.brightness[0];
        break;
      // Needed for initial property setting, can be ignored further.
      case "initialProperty":
        break;
      // Error handling for unsupported properties
      default:
        console.warn(`Unsupported property: ${property}`);
        break;
    }
  });
}
