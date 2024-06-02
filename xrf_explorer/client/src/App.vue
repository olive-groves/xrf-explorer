<script setup lang="ts">
import { provide } from "vue";
import { Header } from "@/components/menus";
import { WindowContainer } from "@/components/ui/window";
import { ImageViewer } from "@/components/image-viewer";
import { Toaster } from "@/components/ui/sonner";
import { FrontendConfig } from "./lib/config";

// Import all windows
import { LayerWindow } from "@/windows/layer-window";
import { WorkspaceWindow } from "./windows/workspace-window";
import { DRWindow, ChartWindow, SpectraWindow, ElementalChannelWindow } from "@/windows";

// Import all reusable dialogs
import { UploadFileDialog } from "@/components/dialogs";
import BaseContextMenu from "./components/menus/BaseContextMenu.vue";

// Provide configuration to app
const props = defineProps<{
  /**
   * The config to be used by the client.
   */
  config: FrontendConfig;
}>();
provide("config", props.config);
console.info("XRF-Explorer client created with configuration: ", props.config);
</script>

<template>
  <Toaster position="top-center" />
  <BaseContextMenu>
    <div class="grid h-screen w-screen grid-cols-1 grid-rows-[min-content_1fr]">
      <Header />
      <WindowContainer>
        <ImageViewer />

        <!-- Place all windows below here -->
        <ElementalChannelWindow />
        <LayerWindow />
        <WorkspaceWindow />
        <ChartWindow />
        <DRWindow />
        <SpectraWindow />
      </WindowContainer>

      <!-- Place all reusable dialogs here -->
      <UploadFileDialog />
    </div>
  </BaseContextMenu>
</template>
