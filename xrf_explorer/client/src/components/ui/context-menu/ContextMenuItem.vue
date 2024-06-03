<script setup lang="ts">
import { type HTMLAttributes, computed } from "vue";
import { ContextMenuItem, type ContextMenuItemEmits, type ContextMenuItemProps, useForwardPropsEmits } from "radix-vue";
import { cn } from "@/lib/utils";

const props = defineProps<
  ContextMenuItemProps & {
    // eslint-disable-next-line vue/require-prop-comment
    class?: HTMLAttributes["class"];
    /**
     * Whether this menu item should be inset.
     */
    inset?: boolean;
  }
>();
const emits = defineEmits<ContextMenuItemEmits>();

const delegatedProps = computed(() => {
  const { class: _, ...delegated } = props;

  return delegated;
});

const forwarded = useForwardPropsEmits(delegatedProps, emits);
</script>

<template>
  <ContextMenuItem
    v-bind="forwarded"
    :class="
      cn(
        `relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none
        focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50`,
        inset && 'pl-8',
        props.class,
      )
    "
  >
    <slot />
  </ContextMenuItem>
</template>
