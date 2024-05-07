<script setup lang="ts">
import { ScrollArea } from '../scroll-area';
import { onBeforeUnmount, onMounted, ref } from 'vue';
import { windowState } from './state';
import { useResizeObserver } from '@vueuse/core';

const props = defineProps<{
  windowId: string,
  areaHeight: number
}>();

const state = windowState[props.windowId];

const emit = defineEmits(['contentHeight'])
const content = ref<HTMLElement | null>(null);
useResizeObserver(content, (entries) => {
  const entry = entries[0];
  emit('contentHeight', entry.contentRect.height);
})

onMounted(() => {
  state.portalMounted = true;
});

onBeforeUnmount(() => {
  state.portalMounted = false;
});
</script>

<template>
  <ScrollArea :style="{
    height: state.scrollable ? `${props.areaHeight}px` : 'min-content'
  }">
    <div ref="content" :id="`window-${state.id}`" />
  </ScrollArea>
</template>