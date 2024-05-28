<script setup lang="ts">
import { provide } from "vue";
import { Header } from "@/components";
import { WindowContainer } from "@/components/ui/window";
import { ImageViewer } from "@/components/image-viewer";
import { FrontendConfig } from "./lib/config";

// Import all windows
import { LayerWindow } from "@/windows/layer-window";
import { WorkspaceWindow } from "./windows/workspace-window";
import { DRWindow, BarChartWindow, SpectraWindow, ElementalChannelWindow } from "@/windows";

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
console.log("XRF-Explorer client created with configuration: ", props.config);

// Set up a default workspace
// Temporary: Needs to be moved to the file menu in a later PR
import { WorkspaceConfig } from "./lib/workspace";
import { appState } from "./lib/appState";
const workspace: WorkspaceConfig = {
  name: "Amandelbloesem",
  baseImage: {
    name: "RGB",
    imageLocation: "base.png",
    recipeLocation: "",
  },
  contextualImages: [
    {
      name: "UV",
      imageLocation: "uv.png",
      recipeLocation: "recipe_uv.csv",
    },
    {
      name: "Xray",
      imageLocation: "xray.png",
      recipeLocation: "recipe_xray.csv",
    },
  ],
  spectralCubes: [
    {
      name: "Datacube",
      rawLocation: "spectral.raw",
      rplLocation: "spectral.rpl",
      recipeLocation: "spectral_cube.json",
    },
  ],
  elementalCubes: [
    {
      name: "Datacube",
      fileType: "dms",
      dataLocation: "elemental.dms",
      recipeLocation: "spectral_cube.json",
    },
  ],
  elementalChannels: [],
};
for (let i = 0; i < 26; i++) {
  workspace.elementalChannels.push({
    name: `element_${i}`,
    channel: i,
    enabled: true,
  });
}
appState.workspace = workspace;
</script>

<template>
  <div class="grid h-screen w-screen grid-cols-1 grid-rows-[min-content_1fr]">
    <Header />
    <WindowContainer>
      <ImageViewer />

      <!-- Place all windows below here -->
      <ElementalChannelWindow />
      <LayerWindow />
      <WorkspaceWindow />
      <BarChartWindow />
      <DRWindow />
      <SpectraWindow />
    </WindowContainer>

    <!-- Place all reusable dialogs here -->
    <UploadFileDialog />
  </div>
</template>
