<script setup lang="ts">
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import { Teleport, toRef } from "vue";
import { WindowLocation, windowState } from "./state";
import { snakeCase } from "change-case";

const props = defineProps<{
  /**
   * The title of the window, must be unique.
   */
  title: string;
  /**
   * Whether or not to open the window by default.
   */
  opened?: boolean;
  /**
   * Whether or not to allow scrolling inside the window.
   *
   * Enabling noScroll could be useful for fixed size content such as charts.
   */
  noScroll?: boolean;
  /**
   * The default location for the window.
   */
  location?: WindowLocation;
}>();

const id = snakeCase(props.title);

if (!(id in windowState)) {
  windowState[id] = {
    id: id,
    title: props.title,
    scrollable: !props.noScroll,
    opened: props.opened ?? false,
    location: props.location ?? "left",
    portalMounted: false,
  };
}

const state = toRef(windowState, id);
</script>

<template>
  <Teleport :to="`#window-${state.id}`" v-if="state.portalMounted">
    <slot />
  </Teleport>
</template>
