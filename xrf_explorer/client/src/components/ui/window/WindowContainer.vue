<script setup lang="ts">
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable";
import { windowState } from "./state";
import { WindowSidepanel } from ".";
import { computed } from "vue";
import { useWindowSize } from "@vueuse/core";
import { remToPx } from "@/lib/utils";

const leftWindows = computed(() =>
  Object.keys(windowState).filter((key) => windowState[key].opened && windowState[key].location == "left"),
);

const rightWindows = computed(() =>
  Object.keys(windowState).filter((key) => windowState[key].opened && windowState[key].location == "right"),
);

const { width } = useWindowSize();
const collapsedSize = computed(() => (100 * remToPx(1)) / width.value);
</script>

<template>
  <ResizablePanelGroup direction="horizontal">
    <ResizablePanel :default-size="20" :min-size="10" collapsible :collapsed-size="collapsedSize">
      <WindowSidepanel :windows="leftWindows" />
    </ResizablePanel>
    <ResizableHandle with-handle />
    <ResizablePanel :min-size="20">
      <slot />
    </ResizablePanel>
    <ResizableHandle with-handle />
    <ResizablePanel :default-size="20" :min-size="10" collapsible :collapsed-size="collapsedSize">
      <WindowSidepanel :windows="rightWindows" />
    </ResizablePanel>
  </ResizablePanelGroup>
</template>
