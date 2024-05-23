<script setup lang="ts">
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable";
import { windowState } from "./state";
import { WindowSidepanel } from ".";
</script>

<template>
  <ResizablePanelGroup direction="horizontal">
    <ResizablePanel :default-size="20" :min-size="10">
      <WindowSidepanel
        :windows="
          Object.keys(windowState).filter((key) => windowState[key].opened && windowState[key].location == 'left')
        "
      />
    </ResizablePanel>
    <ResizableHandle />
    <ResizablePanel :min-size="10">
      <slot />
    </ResizablePanel>
    <ResizableHandle />
    <ResizablePanel :default-size="20" :min-size="10">
      <WindowSidepanel
        :windows="
          Object.keys(windowState).filter((key) => windowState[key].opened && windowState[key].location == 'right')
        "
      />
    </ResizablePanel>
  </ResizablePanelGroup>
</template>
