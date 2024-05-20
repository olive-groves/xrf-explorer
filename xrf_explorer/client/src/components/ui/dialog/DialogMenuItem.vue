<script setup lang="ts">
import { MenubarItem } from "../menubar";
import { openDialog } from "./utils";

const props = defineProps<{
  /**
   * The id of the dialog that should be opened by clicking on this menu item.
   */
  id: string;
}>();
</script>

<template>
  <MenubarItem @click="openDialog(props.id)">
    <slot />
  </MenubarItem>
</template>
