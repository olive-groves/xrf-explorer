<script setup lang="ts">
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable";
import { windowState } from "./state";
import { WindowSidepanel } from ".";
import { computed } from "vue";

const leftWindows = computed(() =>
  Object.keys(windowState).filter((key) => windowState[key].opened && windowState[key].location == "left"),
);

const rightWindows = computed(() =>
  Object.keys(windowState).filter((key) => windowState[key].opened && windowState[key].location == "right"),
);
</script>

<template>
  <ResizablePanelGroup direction="horizontal">
    <ResizablePanel :default-size="20" :min-size="10">
      <WindowSidepanel :windows="leftWindows" />
    </ResizablePanel>
    <ResizableHandle />
    <ResizablePanel :min-size="10">
      <slot />
    </ResizablePanel>
    <ResizableHandle />
    <ResizablePanel :default-size="20" :min-size="10">
      <WindowSidepanel :windows="rightWindows" />
    </ResizablePanel>
  </ResizablePanelGroup>
</template>
