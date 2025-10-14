<script setup lang="ts">
// Import the necessary functions and components
import { ref, toRef, watch } from "vue";
import { WindowLocation, windowState } from "./state";
import { snakeCase } from "change-case";
import { appState } from "@/lib/appState";

const props = defineProps<{
  /**
   * The title of the window, must be unique.
   */
  title: string;
  /**
   * Whether the window is disabled.
   */
  disabled?: boolean;
  /**
   * Whether to open the window by default.
   */
  opened?: boolean;
  /**
   * Whether to allow scrolling inside the window.
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

// Initialize the window state if it doesn't exist
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

// Set the opened state
const disabled = toRef(props, "disabled");
watch(disabled, (value) => (windowState[id].disabled = value));

// Define the window state
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

// Open Stitching window when stitching starts
watch(
  () => appState.stitching,
  (isStitching) => {
    if (isStitching && state.value.id == "stitching") {
      windowState[state.value.id].disabled = false;
      windowState[state.value.id].opened = true;
    }
    else if (isStitching && state.value.id !== "stitching") {
      windowState[state.value.id].opened = false;
      windowState[state.value.id].disabled = true;
    }
  },
  { immediate: true },
);

// Enable all other windows when stitching is finished
watch(
  () => appState.stitching,
  (isStitching) => {
    if (!isStitching && state.value.id != "stitching") {
      windowState[state.value.id].disabled = false; }
  },
  { immediate: false },
);
</script>

<template>
  <Teleport :to="`#window-${state.id}`" v-if="state.portalMounted">
    <div ref="content" v-if="appState.stitching">
      <div v-if="state.id == 'stitching'">
        <slot />
      </div>
      <div v-else class="p-8 text-center text-muted-foreground">Stitching is in-process
      </div>
    </div>
    <div v-else-if="appState.workspace != undefined">
      <slot />
    </div>
    <div v-else class="p-8 text-center text-muted-foreground">No workspace loaded yet.</div> 
  </Teleport>
</template>

