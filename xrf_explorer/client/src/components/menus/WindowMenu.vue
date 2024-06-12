<script setup lang="ts">
import {
  MenubarCheckboxItem,
  MenubarContent,
  MenubarItem,
  MenubarMenu,
  MenubarTrigger,
  MenubarSeparator,
} from "@/components/ui/menubar";
import { windowState } from "@/components/ui/window/state";
import { secondViewer } from "@/lib/appState";
import { computed, useSlots } from "vue";
import { toast } from "vue-sonner";

const slots = useSlots();
const hasSlot = computed(() => {
  return "default" in slots;
});

/**
 * Function to enable/disable the second viewer.
 */
function enableSecondViewer() {
  secondViewer.value = !secondViewer.value;
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
      <MenubarItem @click="enableSecondViewer">Second main viewer</MenubarItem>
    </MenubarContent>
  </MenubarMenu>
</template>
