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

// We have a single bitmaks that we update, so width = 1
const width = 1;
// Arbitrary amount, needs to be greater than maximum number of clusters.
const height = 64;
// One data entry for each of the elements + one for the whole picture
const data = new Uint8Array(width * height * 4);
const dataTexture = createDataTexture(data, width, height);

watch(selection, selectionUpdated, { immediate: true, deep: true });

/**
 * Update image viewer to show updated selection.
 * @param newSelection - The updated selection.
 */
function selectionUpdated(newSelection: ColorSegmentationSelection[]) {
  if (newSelection != undefined) {
    newSelection.enabled.forEach((_, index) => {
      // Get index in texture for cluster at index of element channel.element
      const start = ((index + 1) * width) * 4;

      if (newSelection.enabled[index]) {
        const color = hexToRgb(newSelection.colors[index]);
        data[start + 0] = color[0];
        data[start + 1] = color[1];
        data[start + 2] = color[2];
        data[start + 3] = 255;
      } else {
        data[start + 3] = 0;
      }
    });

    // Create and dispose of layers in accordance with the selection.
    if (layerGroups.value.colorClusters != undefined) {
      layerGroups.value.colorClusters.layers.forEach((layer) => {
        const filename = `${config.api.endpoint}/${datasource.value}/cs/bitmask/${newSelection.element}/${newSelection.k}/${newSelection.threshold}`
        // Only upload image if it changed
        if (layer.image !== filename) {
          disposeLayer(layer);
          layer.image = filename;
          // Important that interpolated = false for the CS layers
          loadLayer(layer, false);
        }
      });
    }
    // Update the data texture in the gpu to reflect possible changes as a result of updating the selection.
    updateDataTexture(layerGroups.value.colorClusters);
  }
}

export async function loadPlaceholderLayer() {
  const recipe = await getRecipe(`${config.api.endpoint}/${datasource.value}/data/recipe`);
  recipe.movingSize = await getDataSize();
  recipe.targetSize = await getTargetSize();

  const layer = createLayer(
    `cs_image`, 
    ``,
    false
  );
  registerLayer(layer, recipe);
  layer.uniform.iLayerType.value = LayerType.ColorSegmentation;
  layer.uniform.iAuxiliary = { value: 0 };
  layer.uniform.tAuxiliary = { value: dataTexture, type: "t" };

  layerGroups.value.colorClusters = {
    name: "Color clusters",
    description: "Generated layer",
    layers: [layer],
    index: -2,
    visible: true,
    ...layerGroupDefaults,
  };
  
  updateLayerGroupLayers(layerGroups.value.colorClusters);
}
