<script setup lang="ts">
import { computed, inject, ref, toRef } from 'vue';
import { z_state } from './z_sorting.ts';
import { clamp, useDraggable, useElementBounding } from '@vueuse/core';

const draggable = ref<HTMLElement | null>(null);
const props = defineProps<{
  id: string,
  handle?: HTMLElement | null,
  x?: number,
  y?: number
}>();
const handle = props.handle === undefined ? draggable : toRef(props, 'handle');
const container = inject<HTMLElement | null>('draggable_container');

z_state[props.id] = 0;

function moveForwards() {
  let count = Object.keys(z_state).length;

  for (let other_id in z_state) {
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
    y: props.y ?? 0
  }
})
const restrictedX = computed(() =>
  clamp(left.value, dragPosition.x.value, right.value - width.value)
);
const restrictedY = computed(() =>
  clamp(top.value, dragPosition.y.value, bottom.value - height.value)
);
</script>

<template>
  <div ref="draggable" @mousedown="moveForwards" class="fixed" :style="{
    'top': `${restrictedY}px`,
    'left': `${restrictedX}px`,
    'z-index': z_state[props.id]
  }">
    <slot />
  </div>
</template>