<script setup lang="ts">
import {
  ContextMenuItem,
  ContextMenuSub,
  ContextMenuSubTrigger,
  ContextMenuSubContent,
  ContextMenuCheckboxItem,
} from "@/components/ui/context-menu";
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
  <ContextMenuItem v-if="panel?.isExpanded" @click="panel?.collapse"> Collapse sidebar </ContextMenuItem>
  <ContextMenuItem v-else @click="panel?.expand">Expand sidebar</ContextMenuItem>
  <ContextMenuSub>
    <ContextMenuSubTrigger> Open window </ContextMenuSubTrigger>
    <ContextMenuSubContent>
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
    </ContextMenuSubContent>
  </ContextMenuSub>
</template>
