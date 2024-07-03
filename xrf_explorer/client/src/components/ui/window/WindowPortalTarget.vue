<script setup lang="ts">
// Import the necessary functions and components
import { ScrollArea } from "../scroll-area";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import { windowState } from "./state";
import { useResizeObserver } from "@vueuse/core";

const props = defineProps<{
  /**
   * The id of the window that should be displayed through this portal.
   */
  windowId: string;
  /**
   * The current height of the window in the side panel, used for setting the height of the scroll area.
   */
  areaHeight: number;
  /**
   * When true, the height of the portal will not decrease, necessary for coherent animations.
   */
  disallowShrink: boolean;
}>();

const state = windowState[props.windowId];

const emit = defineEmits(["contentHeight"]);
const content = ref<HTMLElement | null>(null);
useResizeObserver(content, (entries) => {
  const entry = entries[0];
  emit("contentHeight", entry.contentRect.height);
});

// Set the portal mounted state
onMounted(() => {
  state.portalMounted = true;
});

// Unset the portal mounted state
onBeforeUnmount(() => {
  state.portalMounted = false;
});

/**
 * Set height equal to the areaHeight prop, unless disallowShrink is true and areaHeight is smaller than height.
 */
const height = ref(0);
watch(
  props,
  (value) => {
    if (value.disallowShrink) {
      height.value = Math.max(height.value, value.areaHeight);
    } else {
      height.value = value.areaHeight;
    }
  },
  { deep: true, immediate: true },
);
</script>

<template>
  <ScrollArea
    :style="{
      height: state.scrollable ? `${height}px` : 'min-content',
    }"
  >
    <div ref="content">
      <div class="pb-px" :id="`window-${state.id}`" />
    </div>
  </ScrollArea>
</template>
