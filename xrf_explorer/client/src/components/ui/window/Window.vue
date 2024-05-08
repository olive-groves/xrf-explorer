<script setup lang="ts">
import { Teleport, toRef } from "vue";
import { WindowLocation, windowState } from "./state";
import { snakeCase } from "change-case";

const props = defineProps<{
  title: string,
  opened?: boolean,
  noScroll?: boolean,
  location?: WindowLocation
}>();

const id = snakeCase(props.title);

if (!(id in windowState)) {
  windowState[id] = {
    id: id,
    title: props.title,
    scrollable: !props.noScroll,
    opened: props.opened ?? false,
    location: props.location ?? 'left',
    portalMounted: false
  }
}

const state = toRef(windowState, id);
</script>

<template>
  <Teleport :to="`#window-${state.id}`" v-if="state.portalMounted">
    <slot />
  </Teleport>
</template>