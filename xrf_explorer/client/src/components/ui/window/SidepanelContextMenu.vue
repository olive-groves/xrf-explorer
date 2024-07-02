<script setup lang="ts">
// Import the necessary functions and components
import { ContextMenuItem, ContextMenuSeparator, ContextMenuCheckboxItem } from "@/components/ui/context-menu";
import { ResizablePanel } from "../resizable";
import { WindowLocation, windowState } from "./state";
import { toRef } from "vue";

const panel = defineModel<InstanceType<typeof ResizablePanel>>({ required: true });

const props = defineProps<{
  /**
   * Location of the side panel.
   */
  location: WindowLocation;
}>();

const location = toRef(props, "location");
</script>

<template>
  <ContextMenuItem inset v-if="panel?.isExpanded" @click="panel?.collapse"> Collapse sidebar </ContextMenuItem>
  <ContextMenuItem inset v-else @click="panel?.expand">Expand sidebar</ContextMenuItem>
  <ContextMenuSeparator />
  <ContextMenuCheckboxItem
    v-for="window in windowState"
    :key="window.id"
    :checked="window.opened && window.location == location"
    :disabled="window.disabled"
    @update:checked="
      {
        if (window.opened && window.location == location) {
          window.opened = false;
        } else {
          window.opened = true;
          window.location = location;
        }
      }
    "
  >
    {{ window.title }}
  </ContextMenuCheckboxItem>
</template>
