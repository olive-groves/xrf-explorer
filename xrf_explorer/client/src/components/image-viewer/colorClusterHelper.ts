import { appState } from "@/lib/appState";
import { WorkspaceConfig } from "@/lib/workspace";
import { computed, watch } from "vue";
import { createLayer, layerGroups, updateLayerGroupLayers } from "./state";
import { LayerVisibility } from "./types";
import { createDataTexture, disposeLayer, loadLayer, updateDataTexture } from "./scene";
import { ColorSegmentationSelection } from "@/lib/selection";
import { hexToRgb } from "@/lib/utils";

const selection = computed(() => appState.selection.colorSegmentation);

// TODO: hook up to back end 
// temporary, width should be number of elements plus 1
const width = 27;
// height should be max. number of clusters (currently is 20)
const height = 20;
// One data entry for each of the elements + one for the whole picture
const data = Uint8Array(width * height * 4);
const dataTexture = createDataTexture(data, width, height);

/**
 * Gets the names of the image files for each element.
 */
async function getFilenames(): Promise<{ [key: number]: string }> {
  const filenames: { [key: number]: string } = {};
  for (let i = 0; i < 26; i++) {
    filenames[i] = `elementCluster_${i}.png`;
  }

  // For simplicity, we put the image-wide bitmask last
  filenames[26] = `imageClusters.png`;
  return filenames;
}

/**
 * Creates color segmentation layers (for whole image and element-wise layers).
 *
 * @param workspace
 */
export async function createColorClusterLayers(workspace: WorkspaceConfig) {
  const filenames = await getFilenames();

  // Element-wise color clusters 
  const layers = workspace.elementColorClusters
    .filter((cluster) => cluster.enabled && cluster.channel in filenames)
    .map((cluster) =>
      createLayer(`colorSegmenationElem_${cluster.channel}`, {
        name: `colorSegmenationElem_${cluster.channel}`,
        imageLocation: filenames[cluster.channel],
        recipeLocation: "",
      }),
    );

  // Image-wide color clusters
  if (workspace.colorClusters.enabled && workspace.colorClusters.name in filenames) {
    layers.push(
      createLayer(`colorSegmenationImage`, {
        name: `colorSegmenationImage`,
        imageLocation: filenames.at(-1),
        recipeLocation: ""
      })
    );
  }

  layerGroups.value.colorClusters = {
    type: "colorSegmentation",
    name: "Color clusters",
    description: "",
    layers: layers,
    index: -2,
    visible: true,
    visibility: LayerVisibility.InsideLens,
    opacity: [1.0],
  };

  updateLayerGroupLayers(layerGroups.value.colorClusters);
}
