import { appState } from "@/lib/appState";
import { WorkspaceConfig } from "@/lib/workspace";
import { computed, watch } from "vue";
import { createLayer, layerGroups, updateLayerGroupLayers } from "./state";
import { LayerType, LayerVisibility } from "./types";
import { createDataTexture, updateDataTexture } from "./scene";
import { ElementSelection } from "@/lib/selection";

const selection = computed(() => appState.selection.elements);

const width = 256;
const height = 2;
const data = new Uint8Array(width * height * 4);
const dataTexture = createDataTexture(data, width, height);

watch(selection, selectionUpdated, { immediate: true, deep: true });

/**
 * Update image viewer to show updated selection.
 * @param selection - The updated selection.
 */
function selectionUpdated(selection: ElementSelection[]) {
  selection.forEach((channel) => {
    // Update auxiliary texture
    const start = channel.channel * 4;
    const second = start + width * 4;

    if (channel.selected) {
      data[start + 0] = channel.color[0];
      data[start + 1] = channel.color[1];
      data[start + 2] = channel.color[2];
      data[start + 3] = 255;
      data[second + 0] = Math.round(channel.thresholds[0] * 255);
      data[second + 1] = Math.round(channel.thresholds[1] * 255);
    } else {
      data[start + 3] = 0;
    }
  });

  if (layerGroups.value.elemental != undefined) {
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
  const filenames = await getFilenames();

  const layers = workspace.elementalChannels
    .filter((channel) => channel.enabled && channel.channel in filenames)
    .map((channel) => {
      const layer = createLayer(`elemental_${channel.channel}`, {
        name: `elemental_${channel.channel}`,
        imageLocation: filenames[channel.channel],
        recipeLocation: "",
      });
      layer.uniform.iLayerType.value = LayerType.Elemental;
      layer.uniform.iAuxiliary = { value: channel.channel };
      layer.uniform.tAuxiliary = { value: dataTexture, type: "t" };
      return layer;
    });

  layerGroups.value.elemental = {
    type: "elemental",
    name: "Elemental maps",
    description: "",
    layers: layers,
    index: -2,
    visible: true,
    visibility: LayerVisibility.InsideLens,
    opacity: [1.0],
    contrast: [1.0],
    saturation: [1.0],
  };

  updateLayerGroupLayers(layerGroups.value.elemental);
}
