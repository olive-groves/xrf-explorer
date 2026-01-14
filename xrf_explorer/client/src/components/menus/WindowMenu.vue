<script setup lang="ts">
import {
  MenubarCheckboxItem,
  MenubarContent,
  MenubarMenu,
  MenubarTrigger,
  MenubarSeparator,
} from "@/components/ui/menubar";
import { windowState } from "@/components/ui/window/state";
import { appState } from "@/lib/appState";
import { getTooltipByKey } from "@/lib/useToolTips";
import { computed, useSlots } from "vue";

// Define the slots
// Allow passing content from a parent component to a child component
const slots = useSlots();
const hasSlot = computed(() => {
  return "default" in slots;
});

// Filtered windowState to exclude certain windows for non-admins
const filteredWindows = computed(() => {
  return Object.values(windowState).filter((window) => {
    // Only show the workspace window for admins and editors
    if (window.id === "workspace" || window.id === "stitching") return false;
    return true;
  });
});
</script>

<template>
  <MenubarMenu v-if="appState.user.role !== ''">
    <MenubarTrigger v-if="appState.workspace" class="w-full" v-tooltip="'toolbar.view_menu'"> View </MenubarTrigger>
    <MenubarTrigger v-else class="w-full cursor-not-allowed opacity-50" v-tooltip="'toolbar.workspace_not_loaded'">
      View
    </MenubarTrigger>
    <MenubarContent v-if="appState.workspace">
      <div
        v-for="window in filteredWindows"
        :key="window.id"
        :title="window.disabled ? getTooltipByKey('toolbar.data_missing') : getTooltipByKey('toolbar.' + window.id)"
      >
        <MenubarCheckboxItem v-model:checked="window.opened" :key="window.id" :disabled="window.disabled">
          {{ window.title }}
        </MenubarCheckboxItem>
      </div>
      <MenubarSeparator v-if="hasSlot" />
      <slot />
    </MenubarContent>
  </MenubarMenu>
</template>
