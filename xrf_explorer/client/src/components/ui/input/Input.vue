<script setup lang="ts">
import type { HTMLAttributes } from "vue";
import { useColorMode, useVModel } from "@vueuse/core";
import { cn } from "@/lib/utils";

const props = defineProps<{
  /**
   * The default value of the Input.
   */
  defaultValue?: string | number;
  /**
   * Model describing the value of the input.
   */
  modelValue?: string | number;
  // eslint-disable-next-line vue/require-prop-comment
  class?: HTMLAttributes["class"];
}>();

const emits = defineEmits<{
  (e: "update:modelValue", payload: string | number): void;
}>();

const modelValue = useVModel(props, "modelValue", emits, {
  passive: true,
  defaultValue: props.defaultValue,
});

const colorMode = useColorMode();
</script>

<template>
  <input
    v-model="modelValue"
    :class="
      cn(
        `flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors
        file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground
        focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed
        disabled:opacity-50`,
        props.class,
      )
    "
    :style="{
      'color-scheme': colorMode,
    }"
  />
</template>
