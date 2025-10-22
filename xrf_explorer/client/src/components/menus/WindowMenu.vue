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
import { appState } from "@/lib/appState";

// Define the slots
// Allow passing content from a parent component to a child component
const slots = useSlots();
const hasSlot = computed(() => {
  return "default" in slots;
});

// Check if the user is an admin
const isAdmin = computed(() => appState.user.role === "ADMIN");

// Check if the user is an editor
const isEditor = computed(() => appState.user.role === "EDITOR");

// Filtered windowState to exclude certain windows for non-admins
const filteredWindows = computed(() => {
  return Object.values(windowState).filter(window => {
    // Only show the workspace window for admins and editors
    if (window.id === "workspace" && (!isAdmin.value && !isEditor.value)) return false;
    return true;
  });
});

</script>

<template>
  <MenubarMenu>
    <MenubarTrigger> View </MenubarTrigger>
    <MenubarContent>
      <MenubarCheckboxItem
        v-for="window in filteredWindows"
        v-model:checked="window.opened"
        :disabled="window.disabled"
        :key="window.id"
      >
        {{ window.title }}
      </MenubarCheckboxItem>
      <MenubarSeparator v-if="hasSlot" />
      <slot />
    </MenubarContent>
  </MenubarMenu>
</template>
