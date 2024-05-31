<script setup lang="ts">
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable";
import { windowState } from "./state";
import { SidepanelContextMenu, WindowSidepanel } from ".";
import { computed, ref } from "vue";
import { BaseContextMenu } from "@/components/menus";

const leftWindows = computed(() =>
  Object.keys(windowState).filter((key) => windowState[key].opened && windowState[key].location == "left"),
);

const rightWindows = computed(() =>
  Object.keys(windowState).filter((key) => windowState[key].opened && windowState[key].location == "right"),
);

const leftPanel = ref<InstanceType<typeof ResizablePanel>>();
const rightPanel = ref<InstanceType<typeof ResizablePanel>>();
</script>

<template>
  <ResizablePanelGroup direction="horizontal" class="px-4">
    <ResizablePanel
      ref="leftPanel"
      :default-size="20"
      :min-size="15"
      collapsible
      :collapsed-size="0"
      style="overflow: visible"
    >
      <BaseContextMenu>
        <div class="-ml-4 h-full">
          <WindowSidepanel :windows="leftWindows" />
        </div>
        <template #menu>
          <SidepanelContextMenu location="left" v-model="leftPanel" />
        </template>
      </BaseContextMenu>
    </ResizablePanel>
    <ResizableHandle />
    <ResizablePanel :min-size="20">
      <slot />
    </ResizablePanel>
    <ResizableHandle />
    <ResizablePanel
      ref="rightPanel"
      :default-size="20"
      :min-size="15"
      collapsible
      :collapsed-size="0"
      style="overflow: visible"
    >
      <BaseContextMenu>
        <div class="-mr-4 h-full">
          <WindowSidepanel :windows="rightWindows" />
        </div>
        <template #menu>
          <SidepanelContextMenu location="right" v-model="rightPanel" />
        </template>
      </BaseContextMenu>
    </ResizablePanel>
  </ResizablePanelGroup>
</template>
