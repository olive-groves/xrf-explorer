<script setup lang="ts">
import type { HTMLAttributes } from "vue";
import { MenubarLabel, type MenubarLabelProps } from "radix-vue";
import { cn } from "@/lib/utils";

const props = defineProps<
  MenubarLabelProps & {
    // eslint-disable-next-line vue/require-prop-comment
    class?: HTMLAttributes["class"];
    /**
     * Determines if the label should be inset.
     */
    inset?: boolean;
  }
>();
</script>

<template>
  <MenubarLabel :class="cn('px-2 py-1.5 text-sm font-semibold', inset && 'pl-8', props.class)">
    <slot />
  </MenubarLabel>
</template>
