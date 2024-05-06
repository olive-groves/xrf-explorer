<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue';
import { window_state } from './state';

const props = defineProps<{
  windowId: string
}>();

const state = window_state[props.windowId];

onMounted(() => {
  state.portalMounted = true;
});

onBeforeUnmount(() => {
  state.portalMounted = false;
})
</script>

<template>
  <div :id="`window-${state.id}`" />
</template>