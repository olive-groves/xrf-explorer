<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, onUnmounted} from "vue";
import MappingWindow from "./MappingWindow.vue";
import PreviewWindow from "./PreviewWindow.vue";
import { appState } from "@/lib/appState";

// Wether we are currently mapping points or viewing the preview
const mode = ref<'edit' | 'preview'>(appState.workspace?.mapping.mode ?? 'edit' );

// When the mode changes in StitchViewer also update the mode here
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

// Start in edit mode
onUnmounted(() => {
  mode.value = "edit"
});

</script>

<template>
  <Window title="Stitching" location="right">
    <MappingWindow v-if="mode == 'edit'"></MappingWindow>
    <PreviewWindow v-if="mode == 'preview'"></PreviewWindow>
  </Window>
</template>