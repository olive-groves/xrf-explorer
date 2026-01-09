<script setup lang="ts">
import { provide } from "vue";
import { Header, BaseContextMenu } from "@/components/menus";
import { WindowContainer } from "@/components/ui/window";
import { ImageViewerContainer, StitchViewer } from "@/components/image-viewer";
import { Toaster } from "@/components/ui/sonner";
import { FrontendConfig } from "./lib/config";

// Import all windows
import { LayerWindow } from "@/windows/layer-window";
import FAQWindow from "@/windows/FAQWindow.vue";
import { faqWindowOpen } from "@/lib/windowState";

import { DRWindow, ChartWindow, SpectraWindow, ElementalChannelWindow, CSWindow, StitchWindow } from "@/windows";
import { appState } from "./lib/appState";
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
      <StitchViewer v-if="appState.workspace?.stitchingMode === 'partial'" />
      <ImageViewerContainer v-else />

      <BaseContextMenu>
        <!-- Place all windows below here -->
        <SpectraWindow />
        <ChartWindow />
        <ElementalChannelWindow />
        <CSWindow />
        <DRWindow />
        <LayerWindow />
        <FAQWindow v-if="faqWindowOpen" class="absolute left-0 top-0 z-[9999] size-full bg-background"></FAQWindow>
        <StitchWindow/>
      </BaseContextMenu>
    </WindowContainer>
  </div>
</template>
