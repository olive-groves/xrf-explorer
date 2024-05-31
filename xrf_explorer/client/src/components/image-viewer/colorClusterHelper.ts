import { appState } from "@/lib/appState";
import { computed, watch } from "vue";
import { createLayer, layerGroups, updateLayerGroupLayers } from "./state";
import { LayerType, Layer } from "./types";
import { createDataTexture, disposeLayer, loadLayer, updateDataTexture } from "./scene";
import { ColorSegmentationSelection } from "@/lib/selection";
import { hexToRgb } from "@/lib/utils";
import { layerGroupDefaults } from "./workspace";

const selection = computed(() => appState.selection.colorSegmentation);

const num_elements = 26;
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
    // Get index for cluster channel.channel of element channel.element
    const start = (channel.channel * width + channel.element) * 4;
    if (channel.selected) {
      const color = hexToRgb(channel.color);
      data[start + 0] = color[0];
      data[start + 1] = color[1];
      data[start + 2] = color[2];
      data[start + 3] = 255;
    } else {
      data[start + 3] = 0;
    }
  });

  // Create and dispose of layers in accordance with the selection.
  if (layerGroups.value.elemental != undefined) {
    newSelection.forEach((channel) => {
      // Find the corresponding layer for the element in the selection.
      const layer = layerGroups.value.elemental.layers.filter(
        (layer) => layer.uniform.iAuxiliary!.value == channel.element,
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
    updateDataTexture(layerGroups.value.colorClusters);
  }
}

/**
 * Gets the names of the image files for each element.
 */
async function getFilenames(): Promise<{ [key: number]: string }> {
  const filenames: { [key: number]: string } = {};
  // For simplicity, we put the image-wide bitmask first
  filenames[num_elements] = `imageClusters.png`;

  for (let i = 1; i <= num_elements; i++) {
    filenames[i] = `elementCluster_${i}.png`;
  }

  return filenames;
}

/**
 * Creates color segmentation layers (for whole image and element-wise layers).
 * @param workspace
 */
export async function createColorClusterLayers() {
  const filenames = await getFilenames();

  const layers: Layer[] = [];
  // iAuxiliary passes corresponding element index [0, num_elements - 1]
  for (let i = 1; i <= num_elements; i++) {
      const layer = createLayer(
        `colorSegmenationElem_${i}`,
        {
            name: `colorSegmenationElem_${i-1}`,
            imageLocation: filenames[i],
            recipeLocation: "recipe_cube.csv",
        },
        false,
      );
      layer.uniform.iLayerType.value = LayerType.ColorSegmentation;
      layer.uniform.iAuxiliary = { value: i };
      layer.uniform.tAuxiliary = { value: dataTexture, type: "t" };
      layers.push(layer);
  }
  // Element-wise color clusters
  const layer = createLayer(
    `colorSegmenationImage`,
    {
        name: `colorSegmenationImage`,
        imageLocation: filenames[num_elements],
        recipeLocation: "recipe_cube.csv",
    },
    false,
  );
  layer.uniform.iLayerType.value = LayerType.ColorSegmentation;
  layer.uniform.iAuxiliary = { value: 0 };
  layer.uniform.tAuxiliary = { value: dataTexture, type: "t" };
  layers.push(layer)

  layerGroups.value.colorClusters = {
    name: "Color clusters",
    description: "",
    layers: layers,
    index: -2,
    visible: false,
    ...layerGroupDefaults,
  };

  updateLayerGroupLayers(layerGroups.value.colorClusters);
}
