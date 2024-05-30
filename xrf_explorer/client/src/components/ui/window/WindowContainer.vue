<script setup lang="ts">
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable";
import { windowState } from "./state";
import { WindowSidepanel } from ".";
import { computed, ref } from "vue";
import { BaseContextMenu } from "@/components/menus";
import { ContextMenuItem } from "../context-menu";

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
          <ContextMenuItem v-if="leftPanel?.isExpanded" @click="leftPanel?.collapse">Collapse sidebar</ContextMenuItem>
          <ContextMenuItem v-else @click="leftPanel?.expand">Expand sidebar</ContextMenuItem>
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
          <ContextMenuItem v-if="rightPanel?.isExpanded" @click="rightPanel?.collapse">
            Collapse sidebar
          </ContextMenuItem>
          <ContextMenuItem v-else @click="rightPanel?.expand">Expand sidebar</ContextMenuItem>
        </template>
      </BaseContextMenu>
    </ResizablePanel>
  </ResizablePanelGroup>
</template>
