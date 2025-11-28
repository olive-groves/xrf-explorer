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
import { toast } from "vue-sonner";

// Define the slots
// Allow passing content from a parent component to a child component
const slots = useSlots();
const hasSlot = computed(() => {
  return "default" in slots;
});

/**
 * Function to enable/disable the second viewer.
 */
function toggleSecondViewer() {
  // Update the app state boolean to toggle the second viewer
  appState.secondViewer = !appState.secondViewer;
  toast.info("Viewer layout updated");
}
</script>

<template>
  <MenubarMenu>
    <MenubarTrigger v-tooltip="'toolbar.view_menu'"> View </MenubarTrigger>
    <MenubarContent>
      <div
        v-for="window in windowState"
        :key="window.id"
        :title="window.disabled ? getTooltipByKey('toolbar.data_missing') : getTooltipByKey('toolbar.' + window.id)"
      >
        <MenubarCheckboxItem v-model:checked="window.opened" :key="window.id" :disabled="window.disabled">
          {{ window.title }}
        </MenubarCheckboxItem>
      </div>
      <MenubarSeparator v-if="hasSlot" />
      <slot />
      <MenubarSeparator />
      <MenubarCheckboxItem @click="toggleSecondViewer" :checked="appState.secondViewer"
        >Second main viewer</MenubarCheckboxItem
      >
    </MenubarContent>
  </MenubarMenu>
</template>
