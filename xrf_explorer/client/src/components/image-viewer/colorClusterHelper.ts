import { appState, datasource, elements } from "@/lib/appState";
import { computed, watch } from "vue";
import { createLayer, layerGroups, updateLayerGroupLayers } from "./state";
import { useFetch } from "@vueuse/core";
import { LayerType, Layer } from "./types";
import { createDataTexture, disposeLayer, loadLayer, updateDataTexture } from "./scene";
import { ColorSegmentationSelection } from "@/lib/selection";
import { hexToRgb } from "@/lib/utils";
import { layerGroupDefaults } from "./workspace";
import { getDataSize, getRecipe, getTargetSize } from "./api";
import { registerLayer } from "./registering";
import { config } from "@/main";

const selection = computed(() => appState.selection.colorSegmentation);
const parameters = computed(() => appState.selection.colorSegmentationParameters);

// Arbitrary amount, just needs to be greater than maximum number of elemental channels plus one.
const width = 256;
// Arbitrary amount, needs to be greater than maximum number of clusters.
const height = 32;
// One data entry for each of the elements + one for the whole picture
const data = new Uint8Array(width * height * 4);
const dataTexture = createDataTexture(data, width, height);

watch(selection, selectionUpdated, { immediate: true, deep: true });

/**
 * Update image viewer to show updated selection.
 * @param newSelection - The updated selection.
 */
function selectionUpdated(newSelection: ColorSegmentationSelection[]) {
  newSelection.forEach((channel) => {
    channel.enabled.forEach((_, index) => {
      // Get index for cluster channel.channel of element channel.element
      const start = ((index + 1) * width + channel.element) * 4;

      if (channel.enabled[index]) {
        const color = hexToRgb(channel.colors[index]);
        data[start + 0] = color[0];
        data[start + 1] = color[1];
        data[start + 2] = color[2];
        data[start + 3] = 255;
      } else {
        data[start + 3] = 0;
      }
    });
  });

  // Create and dispose of layers in accordance with the selection.
  if (layerGroups.value.colorClusters != undefined) {
    newSelection.forEach((channel) => {
      // Find the corresponding layer for the element in the selection.
      const layer = layerGroups.value.colorClusters.layers.filter(
        (layer) => layer.uniform.iAuxiliary!.value == channel.element,
      )[0];

      if (layer.mesh == undefined && channel.selected) {
        // If the layer has no mesh/is unloaded, load it into the image viewer if it is selected.
        // Important that interpolated = false for the CS layers
        loadLayer(layer, false);
      } else if (layer.mesh != undefined && !channel.selected) {
        // If the layer has a mesh/is loaded, dispose of it from the image viewer if it is no longer selected.
        disposeLayer(layer);
      }
    });

    // Update the data texture in the gpu to reflect possible changes as a result of updating the selection.
    updateDataTexture(layerGroups.value.colorClusters);
  }
}

/**
 * Gets the names of the image files for each element.
 * @returns List of filenames for each element.
 */
async function getFilenames(): Promise<{ [key: number]: string }> {
  const filenames: { [key: number]: string } = {};

  // For simplicity, we put the image-wide bitmask first
  const { response, data } = await useFetch(
    `${config.api.endpoint}/${datasource.value}/cs/image/bitmask/${parameters.k}/${parameters.k_elem}/${parameters.elem_threshold}`
  )
    .get()
    .blob();

  if (response.value?.ok && data.value != null) {
    filenames[0] = URL.createObjectURL(data.value).toString();
  } else {
    throw new Error("Failed to fetch image CS bitmask.");
  }

  // Bitmasks for element-wise color segments
  for (const element in elements.value) {
    const { response, data } = await useFetch(
      `${config.api.endpoint}/${datasource.value}/cs/element/${element}/bitmask/${parameters.k}/${parameters.k_elem}/${parameters.elem_threshold}`,
    )
      .get()
      .blob();

    if (response.value?.ok && data.value != null) {
      filenames[Number(element) + 1] = URL.createObjectURL(data.value).toString();
    } else {
      throw new Error("Failed to fetch elemental CS bitmasks.");
    }
  }

  return filenames;
}

/**
 * Creates color segmentation layers (for whole image and element-wise layers).
 */
export async function createColorClusterLayers() {
  // const filenames = await getFilenames();
  // const recipe = await getRecipe(`${config.api.endpoint}/${datasource.value}/data/recipe`);
  // recipe.movingSize = await getDataSize();
  // recipe.targetSize = await getTargetSize();

  // const layers: Layer[] = [];
  // // Whole-image color clusters
  // const layer = createLayer(`cs_image`, filenames[0], false);
  // registerLayer(layer, recipe);
  // layer.uniform.iLayerType.value = LayerType.ColorSegmentation;
  // layer.uniform.iAuxiliary = { value: 0 };
  // layer.uniform.tAuxiliary = { value: dataTexture, type: "t" };
  // layers.push(layer);

  // // Element-wise color clusters
  // for (const element in elements.value) {
  //   const layer = createLayer(`cs_element_${element}`, filenames[Number(element) + 1], false);
  //   registerLayer(layer, recipe);
  //   layer.uniform.iLayerType.value = LayerType.ColorSegmentation;
  //   // iAuxiliary passes corresponding element index [1, num_elements]
  //   layer.uniform.iAuxiliary = { value: Number(element) + 1 };
  //   layer.uniform.tAuxiliary = { value: dataTexture, type: "t" };
  //   layers.push(layer);
  // }

  // layerGroups.value.colorClusters = {
  //   name: "Color clusters",
  //   description: "",
  //   layers: layers,
  //   index: -2,
  //   visible: true,
  //   ...layerGroupDefaults,
  // };

  // updateLayerGroupLayers(layerGroups.value.colorClusters);
}
