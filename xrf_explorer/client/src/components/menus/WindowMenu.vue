<script setup lang="ts">
import {
  MenubarCheckboxItem,
  MenubarContent,
  MenubarMenu,
  MenubarTrigger,
  MenubarSeparator,
} from "@/components/ui/menubar";
import { windowState } from "@/components/ui/window/state";
import { computed, useSlots } from "vue";

// Define the slots
// Allow passing content from a parent component to a child component
const slots = useSlots();
const hasSlot = computed(() => {
  return "default" in slots;
});

</script>

<template>
  <MenubarMenu>
    <MenubarTrigger v-tooltip="'Toolbar.view_menu'"> View </MenubarTrigger>
    <MenubarContent>
      <MenubarCheckboxItem
        v-for="window in windowState"
        v-model:checked="window.opened"
        :disabled="window.disabled"
        :key="window.id"
        :title="window.help"
      >
        {{ window.title }}
      </MenubarCheckboxItem>
      <MenubarSeparator v-if="hasSlot" />
      <slot />
    </MenubarContent>
  </MenubarMenu>
</template>
