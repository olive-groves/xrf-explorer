<script setup lang="ts">
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import { Teleport, ref, toRef, watch } from "vue";
import { WindowLocation, windowState } from "./state";
import { snakeCase } from "change-case";
import { appState } from "@/lib/appState";

const props = defineProps<{
  /**
   * The title of the window, must be unique.
   */
  title: string;
  /**
   * Whether or not the window is disabled.
   */
  disabled?: boolean;
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

const emit = defineEmits(["windowMounted", "windowUnmounted"]);

const id = snakeCase(props.title);

if (!(id in windowState)) {
  windowState[id] = {
    id: id,
    title: props.title,
    scrollable: !props.noScroll,
    disabled: props.disabled,
    opened: props.opened ?? false,
    location: props.location ?? "left",
    portalMounted: false,
  };
}

const disabled = toRef(props, "disabled");
watch(disabled, (value) => (windowState[id].disabled = value));

const state = toRef(windowState, id);
const content = ref<HTMLElement | null>(null);

/**
 * Emits the windowMounted event when the window gets mounted.
 * Emits the windowUnmounted event after the window gets unmounted.
 */
watch(
  content,
  (value, oldValue) => {
    if (value != null) {
      emit("windowMounted");
    } else if (oldValue != null) {
      emit("windowUnmounted");
    }
  },
  { immediate: true },
);
</script>

<template>
  <Teleport :to="`#window-${state.id}`" v-if="state.portalMounted">
    <div ref="content" v-if="appState.workspace != undefined">
      <slot />
    </div>
    <div v-else class="p-8 text-center text-muted-foreground">No workspace loaded yet.</div>
  </Teleport>
</template>
