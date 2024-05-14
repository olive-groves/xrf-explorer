<script setup lang="ts">
import { type HTMLAttributes, computed } from "vue";
import { Toggle, type ToggleEmits, type ToggleProps, useForwardPropsEmits } from "radix-vue";
import { type ToggleVariants, toggleVariants } from ".";
import { cn } from "@/lib/utils";

const props = withDefaults(
  defineProps<
    ToggleProps & {
      // eslint-disable-next-line vue/require-prop-comment
      class?: HTMLAttributes["class"];
      /**
       * The variant of the toggle, determines the look of the toggle.
       */
      variant?: ToggleVariants["variant"];
      /**
       * The size of the toggle.
       */
      size?: ToggleVariants["size"];
    }
  >(),
  {
    variant: "default",
    size: "default",
    disabled: false,
  },
);

const emits = defineEmits<ToggleEmits>();

const delegatedProps = computed(() => {
  const { class: _, size: _size, variant: _variant, ...delegated } = props;

  return delegated;
});

const forwarded = useForwardPropsEmits(delegatedProps, emits);
</script>

<template>
  <Toggle v-bind="forwarded" :class="cn(toggleVariants({ variant, size }), props.class)">
    <slot />
  </Toggle>
</template>
