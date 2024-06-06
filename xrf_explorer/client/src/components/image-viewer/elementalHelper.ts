import { appState, datasource } from "@/lib/appState";
import { WorkspaceConfig } from "@/lib/workspace";
import { computed, watch } from "vue";
import { createLayer, layerGroups, updateLayerGroupLayers } from "./state";
import { LayerType } from "./types";
import { createDataTexture, disposeLayer, loadLayer, updateDataTexture } from "./scene";
import { ElementSelection } from "@/lib/selection";
import { hexToRgb } from "@/lib/utils";
import { layerGroupDefaults } from "./workspace";
import { registerLayer } from "./registering";
import { getDataSize, getRecipe, getTargetSize } from "./api";
import { config } from "@/main";

const selection = computed(() => appState.selection.elements);

const width = 256; // Arbitrary amount, just needs to be greater than the maximal amount of elemental channels.
const height = 2; // Top row of pixels will be used to store colors and the bottom to store thresholds.
const data = new Uint8Array(width * height * 4);
const dataTexture = createDataTexture(data, width, height);

watch(selection, selectionUpdated, { immediate: true, deep: true });

/**
 * Update image viewer to show updated selection.
 * @param newSelection - The updated selection.
 */
function selectionUpdated(newSelection: ElementSelection[]) {
  newSelection.forEach((channel) => {
    // Update auxiliary texture
    const start = channel.channel * 4;
    const second = start + width * 4;

    // If channel n is selected, the color at (n, 0) is set to its selected color
    // and the color at (n, 1) contains the thresholds.
    if (channel.selected) {
      const color = hexToRgb(channel.color);
      data[start + 0] = color[0];
      data[start + 1] = color[1];
      data[start + 2] = color[2];
      data[start + 3] = 255;
      data[second + 0] = Math.round(channel.thresholds[0] * 255);
      data[second + 1] = Math.round(channel.thresholds[1] * 255);
    } else {
      data[start + 3] = 0;
    }
  });

  // Create and dispose of layers in accordance with the selection.
  if (layerGroups.value.elemental != undefined) {
    newSelection.forEach((channel) => {
      // Find the corresponding layer for the element in the selection.
      const layer = layerGroups.value.elemental.layers.filter(
        (layer) => layer.uniform.iAuxiliary!.value == channel.channel,
      )[0];

      if (layer.mesh == undefined && channel.selected) {
        // If the layer has no mesh/is unloaded, load it into the image viewer if it is selected.
        loadLayer(layer);
      } else if (layer.mesh != undefined && !channel.selected) {
        // If the layer has a mesh/is loaded, dispose of it from the image viewer if it is no longer selected.
        disposeLayer(layer);
      }
    });

    // Update the data texture in the gpu to reflect possible changes as a result of updating the selection.
    updateDataTexture(layerGroups.value.elemental);
  }
}

/**
 * Gets the names of the image files for each element.
 * @returns The filenames of the elemental maps.
 */
async function getFilenames(): Promise<{ [key: number]: string }> {
  const filenames: { [key: number]: string } = {};
  for (let i = 0; i < 26; i++) {
    filenames[i] = `element_${i}.png`;
  }
  return filenames;
}

/**
 * Loads the workspace into the layer system.
 * @param workspace - The workspace to load into the layer system.
 */
export async function createElementalLayers(workspace: WorkspaceConfig) {
  if (workspace.elementalCubes.length == 0) return;

  const filenames = await getFilenames();
  const recipe = await getRecipe(`${config.api.endpoint}/${datasource.value}/data/recipe`);
  recipe.movingSize = await getDataSize();
  recipe.targetSize = await getTargetSize();

  const layers = workspace.elementalChannels
    .filter((channel) => channel.enabled && channel.channel in filenames)
    .map((channel) => {
      const layer = createLayer(`elemental_${channel.channel}`, filenames[channel.channel], false);
      registerLayer(layer, recipe);
      layer.uniform.iLayerType.value = LayerType.Elemental;
      layer.uniform.iAuxiliary = { value: channel.channel };
      layer.uniform.tAuxiliary = { value: dataTexture, type: "t" };
      return layer;
    });

  layerGroups.value.elemental = {
    name: "Elemental maps",
    description: "Generated layer",
    layers: layers,
    index: -2,
    visible: true,
    ...layerGroupDefaults,
  };

  updateLayerGroupLayers(layerGroups.value.elemental);
}
