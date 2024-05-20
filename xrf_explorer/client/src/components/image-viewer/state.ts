import { ref, watch } from "vue";
import { Layer, LayerGroup } from "./types";
import { ContextualImage } from "@/lib/workspace";
import * as THREE from "three";
import { loadLayer } from "./scene";

/**
 * Contains data for all layers.
 * May not be mutated directly from outside of the ImageViewer.
 */
export const layers = ref<Layer[]>([]);

watch(layers, (n, o) => console.log("layers", n, o), {
  deep: false,
});

/**
 * Describes the different layer groups.
 * May not be mutated directly from outside of the ImageViewer.
 */
export const layerGroups = ref<{
  [key: string]: LayerGroup;
}>({});

watch(layerGroups, (n, o) => console.log("groups", n, o), {
  deep: false,
});

/**
 *
 * @param id
 * @param image
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
    },
  };

  layers.value.push(layer);

  loadLayer(layer);

  return layer;
}

/**
 *
 * @param group
 * @param index
 */
export function setLayerGroupIndex(group: LayerGroup, index: number) {
  group.layers.forEach((layer) => (layer.uniform.iIndex.value = index));
}

/**
 *
 * @param group
 * @param visible
 * @param visibility
 */
export function setLayerGroupVisibility(group: LayerGroup) {
  // TODO: Implement after merging with the lens tool
  // group.layers.forEach((layer) => {
  // })
}
