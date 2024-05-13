<script setup lang="ts">
import { MenubarItem } from "../menubar";
import { openDialog } from "./utils";

const props = defineProps<{
  id: string;
}>();
</script>

<template>
  <MenubarItem @click="openDialog(props.id)">
    <slot />
  </MenubarItem>
</template>
