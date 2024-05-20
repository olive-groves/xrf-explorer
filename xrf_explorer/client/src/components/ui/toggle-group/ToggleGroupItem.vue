<script setup lang="ts">
import type { VariantProps } from "class-variance-authority";
import { type HTMLAttributes, computed, inject } from "vue";
import { ToggleGroupItem, type ToggleGroupItemProps, useForwardProps } from "radix-vue";
import { toggleVariants } from "@/components/ui/toggle";
import { cn } from "@/lib/utils";

type ToggleGroupVariants = VariantProps<typeof toggleVariants>;

const props = defineProps<
  ToggleGroupItemProps & {
    // eslint-disable-next-line vue/require-prop-comment
    class?: HTMLAttributes["class"];
    /**
     * The variant of the toggle group item.
     */
    variant?: ToggleGroupVariants["variant"];
    /**
     * The size of the toggle group item.
     */
    size?: ToggleGroupVariants["size"];
  }
>();

const context = inject<ToggleGroupVariants>("toggleGroup");

const delegatedProps = computed(() => {
  const { class: _, variant: _variant, size: _size, ...delegated } = props;
  return delegated;
});

const forwardedProps = useForwardProps(delegatedProps);
</script>

<template>
  <ToggleGroupItem
    v-bind="forwardedProps"
    :class="
      cn(
        toggleVariants({
          variant: context?.variant || variant,
          size: context?.size || size,
        }),
        props.class,
      )
    "
  >
    <slot />
  </ToggleGroupItem>
</template>
