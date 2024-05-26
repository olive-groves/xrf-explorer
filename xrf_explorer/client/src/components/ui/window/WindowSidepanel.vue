<script setup lang="ts">
import { SidepanelWindowState, windowState } from "./state";
import { computed, ref, watch } from "vue";
import { WindowPortalTarget } from ".";
import { ChevronRight } from "lucide-vue-next";
import { remToPx } from "@/lib/utils";
import { useElementSize } from "@vueuse/core";

const props = defineProps<{
  /**
   * An array of window ids indicating which windows should be displayed in this side panel.
   */
  windows: string[];
}>();

const mounted = ref(false);

const windows = computed(() => {
  // Make sure that tabs are only added after container size is calculated
  if (mounted.value) {
    props.windows.forEach((id) => {
      if (!(id in state.value)) {
        state.value[id] = {
          title: windowState[id].title,
          index: 0,
          minimized: true,
          height: 0,
          maxContentHeight: 0,
        };
      }
    });

    return props.windows;
  } else {
    return [];
  }
});

watch(
  windows,
  (newWindows, oldWindows) => {
    newWindows.forEach((id, index) => {
      if (state.value[id].height == 0) {
        // Perform setup
        console.debug("setting up");
        if (availableHeight < headerSize) {
          shrinkAnyTab(headerSize - availableHeight);
        }
        growTab(id, headerSize);
        removeTarget(id);

        maximize(id);
      }

      // Update the index
      state.value[id].index = index;
    });
    oldWindows.forEach((id) => {
      if (!newWindows.includes(id)) {
        // Clean up window properly
        console.debug("cleaning up", newWindows, oldWindows);
        if (id in state.value) {
          shrinkTab(id, state.value[id].height);
        }
      }
    });
  },
  {
    deep: true,
  },
);

const state = ref<{
  [key: string]: SidepanelWindowState;
}>({});

let totalHeight = 1;
let availableHeight = 1;
const growthTargets: string[] = [];
const shrinkTargets: string[] = [];

const headerSize = remToPx(1.75) + 1;

const container = ref<HTMLElement | null>(null);
const containerSize = useElementSize(container);
watch(containerSize.height, onResize);

const disableAnimation = ref(false);

const mouseState: {
  handle: string;
  dragging: boolean;
} = {
  handle: "",
  dragging: false,
};

/**
 * Either minimizes or maximizes a window.
 * @param id The id of the window that should be minimized or maximized.
 */
function toggleTabSize(id: string) {
  if (state.value[id].minimized) {
    maximize(id);
  } else {
    minimize(id);
  }
}

/**
 * Event handler that handles changes in the window height, making sure that the windows do not take up more vertical
 * height than is visible.
 * @param height The height of the side panel after resizing.
 * @param oldHeight The height of the side panel before resizing.
 */
function onResize(height: number, oldHeight: number) {
  console.debug("onResize", height, oldHeight);
  const growth = height - oldHeight;

  totalHeight += growth;
  console.debug("Updating availableHeight", growth);
  availableHeight += growth;

  disableAnimation.value = true;
  if (growth > 0) {
    growAnyTab(growth);
  } else {
    shrinkAnyTab(-growth);
  }
  disableAnimation.value = false;

  console.debug("Indicating mount");
  mounted.value = true;
}

/**
 * Event handler that handles the resizing of the content of windows, used for setting the maximum height of windows.
 * @param id The window of which the content has been resized.
 * @param height The new size of the content.
 */
function onContentResize(id: string, height: number) {
  console.debug("content", id, height);
  const tab = state.value[id];
  const oldHeight = tab.maxContentHeight;
  const growth = height - oldHeight;
  tab.maxContentHeight = height;

  if (growth > 0) {
    if (!tab.minimized) {
      growTab(id, Math.min(availableHeight, growth));
    }
  } else {
    shrinkTab(id, Math.max(0, tab.height - headerSize - height));
  }
}

/**
 * Maximize a specific window.
 * @param id The id of the window to maximize.
 */
function maximize(id: string) {
  console.debug("maximize", id);
  const tab = state.value[id];

  const openWindows = windows.value.filter((id) => !state.value[id].minimized);

  const allowedHeightShare = Math.round(totalHeight / (openWindows.length + 1));
  const desiredGrowth = Math.min(tab.maxContentHeight, allowedHeightShare);

  const largeWindows: [string, number][] = openWindows.map((id) => [
    id,
    Math.max(state.value[id].height - allowedHeightShare, 0),
  ]);
  const available = largeWindows.reduce((acc, win) => (acc += win[1]), 0);

  const reduction = Math.min(available, Math.max(0, desiredGrowth - availableHeight));

  console.debug(id, desiredGrowth, availableHeight, available, reduction);
  if (available > 0) {
    for (const i in largeWindows) {
      const [tabId, exceededHeight] = largeWindows[i];
      const reduce = Math.round((exceededHeight / available) * reduction);
      shrinkTab(tabId, reduce);
    }
  }

  tab.minimized = false;

  growTab(id, Math.max(desiredGrowth, availableHeight));
}

/**
 * Minimize a specific window.
 * @param id The id of the window to shrink.
 */
function minimize(id: string) {
  console.debug("minimize", id);
  const tab = state.value[id];
  tab.minimized = true;

  const oldHeight = tab.height;
  if (oldHeight > headerSize) {
    shrinkTab(id, oldHeight - headerSize);
    removeTarget(id);
    growAnyTab(oldHeight - headerSize);
  }
  removeTarget(id);
}

/**
 * Grows a specific window by a specific amount.
 * @param id The id of the window to be grown.
 * @param px The amount of pixels by which to grow the window.
 * @returns The amount of pixels by which the window has actually grown.
 */
function growTab(id: string, px: number): number {
  console.debug(`Growing ${id} by ${px}px`);

  const tab = state.value[id];
  const canGrow = Math.min(availableHeight, headerSize + tab.maxContentHeight - tab.height);
  const actualGrowth = Math.min(px, canGrow);

  tab.height += actualGrowth;
  console.debug("Updating availableHeight", actualGrowth);
  availableHeight -= actualGrowth;

  removeTarget(id);
  console.debug(`Adding ${id} as target after growth`);
  growthTargets.unshift(id);
  shrinkTargets.push(id);
  return actualGrowth;
}

/**
 * Shrinks a specific window by a specific amount.
 * @param id The id of the window to be shrunk.
 * @param px The amount of pixels by which to shrink the window.
 * @returns The amount of pixels by which the window has actually shrunk.
 */
function shrinkTab(id: string, px: number): number {
  console.debug(`Shrinking ${id} by ${px}px`);

  const tab = state.value[id];
  const canShrink = tab.height - headerSize;
  const actualShrink = Math.min(px, canShrink);

  tab.height -= actualShrink;
  console.debug("Updating availableHeight", actualShrink);
  availableHeight += actualShrink;

  removeTarget(id);
  if (tab.height <= headerSize && !tab.minimized) {
    stopDragging();
    minimize(id);
  } else {
    console.debug(`Adding ${id} as target after shrink`);
    growthTargets.push(id);
    shrinkTargets.unshift(id);
  }
  return actualShrink;
}

/**
 * Attempts to grow windows until the desired growth has been achieved.
 * @param px The amount of pixels to grow windows by.
 * @param from The index from which windows may be grown (from top to bottom).
 * @returns The realized growth in pixels.
 */
function growAnyTab(px: number, from: number = -1): number {
  console.debug(`Growing any by ${px}px`);
  const targets = [...growthTargets].filter((id) => state.value[id].index > from && !state.value[id].minimized);

  let remaining = px;
  for (let i = 0; i < targets.length; i++) {
    remaining -= growTab(targets[i], remaining);
    if (remaining <= 0) return px;
  }

  return px - remaining;
}

/**
 * Attempts to shrink windows until the desired shrinkage has been achieved.
 * @param px The amount of pixels to shrink windows by.
 * @param from The index from which windows may be shrinked (from top to bottom).
 * @returns The realized shrinkage in pixels.
 */
function shrinkAnyTab(px: number, from: number = -1): number {
  console.debug(`Shrinking any by ${px}px`);
  const targets = [...shrinkTargets].filter((id) => state.value[id].index > from);

  let remaining = px;
  for (let i = 0; i < targets.length; i++) {
    remaining -= shrinkTab(targets[i], remaining);
    if (remaining <= 0) return px;
  }

  return px - remaining;
}

/**
 * Remove an id from both the growthTargets and shrinkTargets arrays.
 * @param id The id to be removed.
 */
function removeTarget(id: string) {
  console.debug(`Removing ${id} from targets`);
  if (growthTargets.includes(id)) {
    growthTargets.splice(growthTargets.indexOf(id), 1);
  }
  if (shrinkTargets.includes(id)) {
    shrinkTargets.splice(shrinkTargets.indexOf(id), 1);
  }
  console.debug(growthTargets, shrinkTargets);
}

/**
 * Start a dragging motion after pressing down on the drag-handle of a window.
 * @param handle The id of the window corresponding to the selected handle.
 */
function startDragging(handle: string) {
  mouseState.dragging = true;
  mouseState.handle = handle;
  disableAnimation.value = true;
}

/**
 * Stops the dragging movement.
 */
function stopDragging() {
  mouseState.dragging = false;
  disableAnimation.value = false;
}

/**
 * Event handler for mouse movement.
 * @param event The MouseEvent to handle.
 */
function handleDragMovement(event: MouseEvent) {
  if (mouseState.dragging) {
    const growth = event.movementY;
    if (growth > 0) {
      console.debug(growth, availableHeight);
      if (growth > availableHeight) {
        shrinkAnyTab(growth - availableHeight, state.value[mouseState.handle].index);
      }
      growTab(mouseState.handle, growth);
    } else {
      shrinkTab(mouseState.handle, -growth);
      growAnyTab(-growth, state.value[mouseState.handle].index);
    }
  }
}
</script>

<template>
  <div
    ref="container"
    class="size-full"
    @mouseleave="stopDragging"
    @mouseup="stopDragging"
    @mousemove="handleDragMovement"
  >
    <div
      class="grid max-h-full grid-cols-1"
      style="grid-template-rows: repeat(1, minmax(calc(1.75rem + 1px), max-content))"
    >
      <template v-for="id in windows" :key="id">
        <div
          class="z-0 overflow-hidden duration-100"
          :style="{
            height: `${state[id].height}px`,
          }"
          :class="{
            'transition-all': !disableAnimation,
            'transition-none': disableAnimation,
          }"
        >
          <div
            @click="toggleTabSize(id)"
            class="left-0 flex w-full cursor-pointer justify-start space-x-1 whitespace-nowrap border-b p-1"
          >
            <ChevronRight
              class="size-5 min-w-5 duration-100"
              :class="{
                'rotate-90': !state[id].minimized,
              }"
            />
            <div class="font-bold">
              {{ state[id].title }}
            </div>
          </div>
          <div
            class="-mt-px overflow-hidden"
            :style="{
              height: `${state[id].minimized ? '0px' : `${state[id].height - headerSize}px`}`,
            }"
          >
            <WindowPortalTarget
              ref="contentRefs"
              :window-id="id"
              @content-height="(entry) => onContentResize(id, entry)"
              :area-height="state[id].height - headerSize"
            />
          </div>
        </div>
        <div v-if="!state[id].minimized" @mousedown="startDragging(id)" class="z-10 -my-1 h-2 w-full cursor-ns-resize">
          <div class="mt-[calc(0.25rem-1px)] h-px bg-border" />
        </div>
      </template>
    </div>
  </div>
</template>
