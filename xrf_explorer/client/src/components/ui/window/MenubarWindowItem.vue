<script setup lang="ts">
import { window_state } from '@/components/ui/window/state';
import { defineProps } from 'vue';
import { MenubarCheckboxItem } from '@/components/ui/menubar';

const props = defineProps<{
  window_id: string,
}>();

if (!Object.hasOwn(window_state.windows, props.window_id)) {
  window_state.windows[props.window_id] = {
    is_opened: true,
    z_index: 0
  };
}

</script>

<template>
  <MenubarCheckboxItem v-model:checked="window_state.windows[props.window_id].is_opened">
    <slot />
  </MenubarCheckboxItem>
</template>