<script setup lang="ts">
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable";
import { windowState } from "./state";
import { SidepanelContextMenu, WindowSidepanel } from ".";
import { computed, ref } from "vue";
import { BaseContextMenu } from "@/components/menus";
import { remToPx } from "@/lib/utils";

const leftWindows = computed(() =>
  Object.keys(windowState).filter((key) => windowState[key].opened && windowState[key].location == "left"),
);

const rightWindows = computed(() =>
  Object.keys(windowState).filter((key) => windowState[key].opened && windowState[key].location == "right"),
);

const leftPanel = ref<InstanceType<typeof ResizablePanel>>();
const rightPanel = ref<InstanceType<typeof ResizablePanel>>();

const hitArea = {
  coarse: remToPx(1.5),
  fine: remToPx(0.5),
};
</script>

<template>
  <ResizablePanelGroup direction="horizontal" class="px-0">
    <ResizablePanel
      ref="leftPanel"
      :default-size="20"
      :min-size="0"
      collapsible
      :collapsed-size="0"
      style="overflow: visible"
    >
      <BaseContextMenu>
        <div class="-ml-0 h-full">
          <WindowSidepanel :windows="leftWindows" />
        </div>
        <template #menu>
          <SidepanelContextMenu location="left" v-model="leftPanel" />
        </template>
      </BaseContextMenu>
    </ResizablePanel>
    <ResizableHandle :hit-area-margins="hitArea" />
    <ResizablePanel :min-size="20">
      <slot />
    </ResizablePanel>
    <ResizableHandle :hit-area-margins="hitArea" />
    <ResizablePanel
      ref="rightPanel"
      :default-size="20"
      :min-size="0"
      collapsible
      :collapsed-size="0"
      style="overflow: visible"
    >
      <BaseContextMenu>
        <div class="-mr-0 h-full">
          <WindowSidepanel :windows="rightWindows" />
        </div>
        <template #menu>
          <SidepanelContextMenu location="right" v-model="rightPanel" />
        </template>
      </BaseContextMenu>
    </ResizablePanel>
  </ResizablePanelGroup>
</template>
