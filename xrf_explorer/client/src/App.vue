<script setup lang="ts">
import { provide } from "vue";
import { Header, BaseContextMenu } from "@/components/menus";
import { WindowContainer } from "@/components/ui/window";
import { ImageViewerContainer } from "@/components/image-viewer";
import { Toaster } from "@/components/ui/sonner";
import { FrontendConfig } from "./lib/config";

// Import all windows
import { LayerWindow } from "@/windows/layer-window";
import { WorkspaceWindow } from "./windows/workspace-window";
import { DRWindow, ChartWindow, SpectraWindow, ElementalChannelWindow, CSWindow } from "@/windows";

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
  <div class="grid h-screen w-screen grid-cols-1 grid-rows-[min-content_1fr]">
    <Header />
    <WindowContainer>
      <ImageViewerContainer />

      <BaseContextMenu>
        <!-- Place all windows below here -->
        <SpectraWindow />
        <ChartWindow />
        <ElementalChannelWindow />
        <CSWindow />
        <DRWindow />
        <LayerWindow />
        <WorkspaceWindow />
      </BaseContextMenu>
    </WindowContainer>
  </div>
</template>
