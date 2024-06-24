<script setup lang="ts">
import { ContextMenu, ContextMenuContent, ContextMenuTrigger } from "@/components/ui/context-menu";

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
</script>

<template>
  <ContextMenu>
    <ContextMenuTrigger>
      <slot />
    </ContextMenuTrigger>
    <ContextMenuContent>
      <slot name="menu" />
    </ContextMenuContent>
  </ContextMenu>
</template>
