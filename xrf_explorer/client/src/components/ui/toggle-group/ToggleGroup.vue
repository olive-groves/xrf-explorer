<script setup lang="ts">
import type { VariantProps } from "class-variance-authority";
import { type HTMLAttributes, computed, provide } from "vue";
import { ToggleGroupRoot, type ToggleGroupRootEmits, type ToggleGroupRootProps, useForwardPropsEmits } from "radix-vue";
import type { toggleVariants } from "@/components/ui/toggle";
import { cn } from "@/lib/utils";

type ToggleGroupVariants = VariantProps<typeof toggleVariants>;

const props = defineProps<
  ToggleGroupRootProps & {
    // eslint-disable-next-line vue/require-prop-comment
    class?: HTMLAttributes["class"];
    /**
     * The variant of the toggles in the toggle group.
     */
    variant?: ToggleGroupVariants["variant"];
    /**
     * The size of the toggles in the toggle group.
     */
    size?: ToggleGroupVariants["size"];
  }
>();
const emits = defineEmits<ToggleGroupRootEmits>();

provide("toggleGroup", {
  variant: props.variant,
  size: props.size,
});

const delegatedProps = computed(() => {
  const { class: _, ...delegated } = props;
  return delegated;
});

const forwarded = useForwardPropsEmits(delegatedProps, emits);
</script>

<template>
  <ToggleGroupRoot v-bind="forwarded" :class="cn('flex items-center justify-center gap-1', props.class)">
    <slot />
  </ToggleGroupRoot>
</template>
