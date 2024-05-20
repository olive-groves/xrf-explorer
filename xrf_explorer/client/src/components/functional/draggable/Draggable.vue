<script setup lang="ts">
import { computed, inject, ref, toRef } from "vue";
import { z_state } from "./z_sorting.ts";
import { clamp, useDraggable, useElementBounding } from "@vueuse/core";

const draggable = ref<HTMLElement | null>(null);
const props = defineProps<{
  /**
   * The id of the draggable component, must be unique.
   */
  id: string;
  /**
   * An element to use as handle for the draggable component.
   */
  handle?: HTMLElement | null;
  /**
   * The default x coordinate of the draggable component.
   */
  x?: number;
  /**
   * The default y coordinate of the draggable component.
   */
  y?: number;
}>();
const handle = props.handle === undefined ? draggable : toRef(props, "handle");
const container = inject<HTMLElement | null>("draggable_container");

z_state[props.id] = 0;

/**
 * Increases the z-index of this component and decreases the z-index of all others.
 */
function moveForwards() {
  const count = Object.keys(z_state).length;

  for (const other_id in z_state) {
    if (z_state[other_id] > z_state[props.id]) {
      z_state[other_id]--;
    }
  }

  z_state[props.id] = count - 1;
}

const { left, right, top, bottom } = useElementBounding(container);
const { width, height } = useElementBounding(draggable);
const dragPosition = useDraggable(draggable, {
  handle: handle,
  initialValue: {
    x: props.x ?? 0,
    y: props.y ?? 0,
  },
});
const restrictedX = computed(() => clamp(left.value, dragPosition.x.value, right.value - width.value));
const restrictedY = computed(() => clamp(top.value, dragPosition.y.value, bottom.value - height.value));
</script>

<template>
  <div
    ref="draggable"
    @mousedown="moveForwards"
    class="fixed"
    :style="{
      top: `${restrictedY}px`,
      left: `${restrictedX}px`,
      'z-index': z_state[props.id],
    }"
  >
    <slot />
  </div>
</template>
