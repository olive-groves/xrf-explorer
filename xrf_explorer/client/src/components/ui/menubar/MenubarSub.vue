<script setup lang="ts">
import { MenubarSub, type MenubarSubEmits, useForwardPropsEmits } from "radix-vue";

interface MenubarSubRootProps {
  /**
   * Determines whether the submenu should be open by default.
   */
  defaultOpen?: boolean;
  /**
   * Determines whether the submenu should be open or not, can be bound for more control.
   */
  open?: boolean;
}

const props = defineProps<MenubarSubRootProps>();
const emits = defineEmits<MenubarSubEmits>();

const forwarded = useForwardPropsEmits(props, emits);
</script>

<template>
  <MenubarSub v-bind="forwarded">
    <slot />
  </MenubarSub>
</template>
