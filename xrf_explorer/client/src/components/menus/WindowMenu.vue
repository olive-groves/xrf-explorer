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
import { computed, useSlots } from "vue";
import { toast } from "vue-sonner";

const slots = useSlots();
const hasSlot = computed(() => {
  return "default" in slots;
});

/**
 * Function to enable/disable the second viewer.
 */
function toggleSecondViewer() {
  appState.secondViewer = !appState.secondViewer;
  toast.info("Viewer layout updated");
}
</script>

<template>
  <MenubarMenu>
    <MenubarTrigger> View </MenubarTrigger>
    <MenubarContent>
      <MenubarCheckboxItem v-for="window in windowState" v-model:checked="window.opened" :key="window.id">
        {{ window.title }}
      </MenubarCheckboxItem>
      <MenubarSeparator v-if="hasSlot" />
      <slot />
      <MenubarSeparator />
      <MenubarCheckboxItem @click="toggleSecondViewer">Second main viewer</MenubarCheckboxItem>
    </MenubarContent>
  </MenubarMenu>
</template>
