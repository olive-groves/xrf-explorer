<script setup lang="ts">
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuSeparator,
  ContextMenuTrigger,
} from "@/components/ui/context-menu";
import { resetWindow } from "@/lib/utils";
import { computed, useSlots } from "vue";

/**
 * The base context menu, if a specific component needs to add additional components to this menu,
 * wrap the component in <BaseContextMenu /> and put the additional context menu items in <template #menu />.
 * ```
 * <BaseContextMenu>
 *   <div>Component that needs a context menu</div>
 *   <template #name>
 *     <ContextMenuItem> Additional menuitem </ContextMenuItem>
 *   </template>
 * </BaseContextMenu>.
 * ```
 */

const slots = useSlots();
const hasMenuSlot = computed(() => {
  return "menu" in slots;
});
</script>

<template>
  <ContextMenu>
    <ContextMenuTrigger>
      <slot />
    </ContextMenuTrigger>
    <ContextMenuContent>
      <ContextMenuItem @click="resetWindow"> Reset client </ContextMenuItem>
      <ContextMenuSeparator v-if="hasMenuSlot" />
      <slot name="menu" />
    </ContextMenuContent>
  </ContextMenu>
</template>
