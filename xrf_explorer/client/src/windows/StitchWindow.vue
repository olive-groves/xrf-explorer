<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount} from "vue";
import MappingWindow from "./MappingWindow.vue";
import PreviewWindow from "./PreviewWindow.vue";

const mode = ref<'edit' | 'preview'>('edit');

async function onModeChanged(e: Event | CustomEvent) {
  const newMode = (e as CustomEvent).detail as 'edit' | 'preview';
  mode.value = newMode;
}

onMounted(() => {
  window.addEventListener('stitchViewer:modeChanged', onModeChanged as EventListener);
});

onBeforeUnmount(() => {
  window.removeEventListener('stitchViewer:modeChanged', onModeChanged as EventListener);
});

</script>

<template>
  <window title="stitching" location="right">
    <MappingWindow v-if="mode == 'edit'"></MappingWindow>
    <PreviewWindow v-if="mode == 'preview'"></PreviewWindow>
  </window>
</template>