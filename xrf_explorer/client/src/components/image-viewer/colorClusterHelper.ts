import { appState, datasource } from "@/lib/appState";
import { computed, watch } from "vue";
import { createLayer, layerGroups, updateLayerGroupLayers } from "./state";
import { useFetch } from "@vueuse/core";
import { LayerType, Layer } from "./types";
import { createDataTexture, disposeLayer, loadLayer, updateDataTexture } from "./scene";
import { ColorSegmentationSelection } from "@/lib/selection";
import { hexToRgb } from "@/lib/utils";
// import { FrontendConfig } from "@/lib/config";
import { layerGroupDefaults } from "./workspace";
import { registerLayer } from "./registering";

// const config = inject<FrontendConfig>("config")!;
// We should use config.api.endpoint here instead of hardcoding
const API_ENDPOINT: string = "http://localhost:8001/api";
const selection = computed(() => appState.selection.colorSegmentation);

let num_elements = 26;
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
    const prevStart = (channel.prevChannel * width + channel.element) * 4;
    data[prevStart + 3] = 0;

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

  // Get number of elements
  const response1 = await fetch(`${API_ENDPOINT}/${datasource.value}/get_number_of_elements`);
  if (!response1.ok) {
    throw new Error(`HTTP error! status: ${response1.status}`);
  }
  const responseText = await response1.text();
  num_elements = parseInt(responseText);

  // For simplicity, we put the image-wide bitmask first
  const reqUrl = new URL(`${API_ENDPOINT}/${datasource.value}/get_color_cluster_bitmask`);
  reqUrl.searchParams.set("element", (0).toString());
  const { response, data } = await useFetch(reqUrl.toString()).get().blob();

  if (response.value?.ok && data.value != null) {
    filenames[0] = URL.createObjectURL(data.value).toString();
  } else {
    throw new Error("Failed to fetch colors");
  }

  for (let i = 1; i <= num_elements; i++) {
    const reqUrl = new URL(`${API_ENDPOINT}/${datasource.value}/get_element_color_cluster_bitmask`);
    reqUrl.searchParams.set("element", (i - 1).toString());
    const { response, data } = await useFetch(reqUrl.toString()).get().blob();

    if (response.value?.ok && data.value != null) {
      filenames[i] = URL.createObjectURL(data.value).toString();
    } else {
      throw new Error("Failed to fetch colors");
    }
  }

  return filenames;
}

/**
 * Creates color segmentation layers (for whole image and element-wise layers).
 */
export async function createColorClusterLayers() {
  const filenames = await getFilenames();

  const layers: Layer[] = [];
  // Whole-image color clusters
  const layer = createLayer(`colorSegmenationImage`, filenames[0], false);
  registerLayer(layer, "/recipe_cube.csv");
  layer.uniform.iLayerType.value = LayerType.ColorSegmentation;
  layer.uniform.iAuxiliary = { value: 0 };
  layer.uniform.tAuxiliary = { value: dataTexture, type: "t" };
  layers.push(layer);

  // Element-wise color clusters
  for (let i = 1; i <= num_elements; i++) {
    const layer = createLayer(`colorSegmenationElem_${i}`, filenames[i], false);
    registerLayer(layer, "/recipe_cube.csv");
    layer.uniform.iLayerType.value = LayerType.ColorSegmentation;
    // iAuxiliary passes corresponding element index [1, num_elements]
    layer.uniform.iAuxiliary = { value: i };
    layer.uniform.tAuxiliary = { value: dataTexture, type: "t" };
    layers.push(layer);
  }

  layerGroups.value.colorClusters = {
    name: "Color clusters",
    description: "",
    layers: layers,
    index: -2,
    visible: true,
    ...layerGroupDefaults,
  };

  updateLayerGroupLayers(layerGroups.value.colorClusters);
}
