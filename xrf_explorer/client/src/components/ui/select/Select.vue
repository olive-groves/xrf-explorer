<script setup lang="ts">
// Import the necessary functions and components
import type { SelectRootEmits, SelectRootProps } from "radix-vue";
import { SelectRoot, useForwardPropsEmits } from "radix-vue";

// Define the props and emits
const props = defineProps<SelectRootProps>();
const emits = defineEmits<SelectRootEmits>();

// Forward the props and emits
const forwarded = useForwardPropsEmits(props, emits);
</script>

<template>
  <SelectRoot v-bind="forwarded">
    <slot />
  </SelectRoot>
</template>
