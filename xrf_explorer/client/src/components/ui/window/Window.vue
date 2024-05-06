<script setup lang="ts">
import { Teleport, toRef } from "vue";
import { window_state } from "./state";
import { snakeCase } from "change-case";

const props = defineProps<{
  title: string,
  opened?: boolean
}>();

const id = snakeCase(props.title);

if (!(id in window_state)) {
  window_state[id] = {
    id: id,
    title: props.title,
    opened: props.opened,
    portalMounted: false
  }
}

const state = toRef(window_state, id);
</script>

<template>
  <Teleport :to="`#window-${state.id}`" v-if="state.portalMounted">
    <slot />
  </Teleport>
</template>