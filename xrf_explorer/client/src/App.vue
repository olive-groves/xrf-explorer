<script setup lang="ts">
import { provide } from "vue";
import { Header } from "@/components";
import { WindowContainer } from "@/components/ui/window";
import { ImageViewer } from "@/components/image-viewer";
import { FrontendConfig } from "./lib/config";

// Import all windows
import { LayerWindow } from "@/windows/layer-window";
import { WorkspaceWindow } from "./windows/workspace-window";
import { BarChartWindow } from "@/windows";

// Import all reusable dialogs
import { UploadFileDialog } from "@/components/dialogs";

// Provide configuration to app
const props = defineProps<{
  /**
   * The config to be used by the client.
   */
  config: FrontendConfig;
}>();
provide("config", props.config);
console.log("Client created with configuration: ", props.config);

// Set up a default workspace
// Temporary: Needs to be moved to the file menu in a later PR
import { WorkspaceConfig } from "./lib/workspace";
import { appState } from "./lib/app_state";
const workspace: WorkspaceConfig = {
  name: "Amandelbloesem",
  baseImage: {
    name: "RGB",
    imageLocation:
      "https://upload.wikimedia.org/wikipedia/commons/8/80/Amandelbloesem_-_s0176V1962_-_Van_Gogh_Museum.jpg",
    recipeLocation: "",
  },
  contextualLayers: [
    {
      name: "UV",
      imageLocation:
        "https://upload.wikimedia.org/wikipedia/commons/3/37/M%C3%BCnster%2C_LWL-Museum_f%C3%BCr_Kunst_und_Kultur%2C_Lichtkunstwerk_%22Silberne_Frequenz%22_--_2022_--_4266.jpg?download",
      recipeLocation: "",
    },
    {
      name: "Xray",
      imageLocation:
        "https://upload.wikimedia.org/wikipedia/commons/3/37/M%C3%BCnster%2C_LWL-Museum_f%C3%BCr_Kunst_und_Kultur%2C_Lichtkunstwerk_%22Silberne_Frequenz%22_--_2022_--_4266.jpg?download",
      recipeLocation: "",
    },
  ],
  spectralCubes: [],
  elementalCubes: [],
};
appState.workspace = workspace;
</script>

<template>
  <div class="grid h-screen w-screen grid-cols-1 grid-rows-[min-content_1fr]">
    <Header />
    <WindowContainer>
      <ImageViewer />

      <!-- Place all windows below here -->
      <LayerWindow />
      <WorkspaceWindow />
      <BarChartWindow />
    </WindowContainer>

    <!-- Place all reusable dialogs here -->
    <UploadFileDialog />
  </div>
</template>
