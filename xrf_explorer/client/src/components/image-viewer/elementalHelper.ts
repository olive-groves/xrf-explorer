import { appState } from "@/lib/appState";
import { WorkspaceConfig } from "@/lib/workspace";
import { computed, watch } from "vue";
import { createLayer, layerGroups, updateLayerGroupLayers } from "./state";
import { LayerVisibility } from "./types";

const selection = computed(() => appState.selection.elements);

watch(selection, () => console.log);

/**
 * Gets the names of the image files for each element.
 */
async function getFilenames(): Promise<{ [key: number]: string }> {
  const filenames: { [key: number]: string } = {};
  for (let i = 0; i < 26; i++) {
    filenames[i] = `element_${i}.png`;
  }
  return filenames;
}

/**
 *
 * @param workspace
 */
export async function createElementalLayers(workspace: WorkspaceConfig) {
  const filenames = await getFilenames();

  const layers = workspace.elementalChannels
    .filter((channel) => channel.enabled && channel.channel in filenames)
    .map((channel) =>
      createLayer(`elemental_${channel.channel}`, {
        name: `elemental_${channel.channel}`,
        imageLocation: filenames[channel.channel],
        recipeLocation: "",
      }),
    );

  layerGroups.value.elemental = {
    type: "elemental",
    name: "Elemental maps",
    description: "",
    layers: layers,
    index: -2,
    visible: true,
    visibility: LayerVisibility.InsideLens,
    opacity: [1.0],
  };

  updateLayerGroupLayers(layerGroups.value.elemental);
}
