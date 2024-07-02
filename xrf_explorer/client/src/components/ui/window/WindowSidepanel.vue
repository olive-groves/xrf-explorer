<script setup lang="ts">
// Import the necessary functions and components
import { SidepanelWindowState, windowState } from "./state";
import { computed, ref, watch } from "vue";
import { WindowPortalTarget } from ".";
import { ChevronRight } from "lucide-vue-next";
import { remToPx } from "@/lib/utils";
import { useElementSize } from "@vueuse/core";
import { BaseContextMenu } from "@/components/menus";
import { ContextMenuItem, ContextMenuRadioGroup, ContextMenuRadioItem, ContextMenuSeparator } from "../context-menu";

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
    // Return an empty array if the component is not mounted yet
    return [];
  }
});

watch(
  windows,
  (newWindows, oldWindows) => {
    // Update the index of each window
    newWindows.forEach((id, index) => {
      if (state.value[id].height == 0) {
        // Perform setup
        console.debug("Setting up window", id);
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
    // Clean up windows that are no longer present
    oldWindows.forEach((id) => {
      if (!newWindows.includes(id)) {
        // Clean up window properly
        console.debug("Cleaning up window", id);
        if (id in state.value) {
          removeTarget(id);
          const height = state.value[id].height;
          availableHeight += height;
          console.debug("Available height increased by ", height);
          growAnyTab(height);
          state.value[id].height = 0;
        }
      }
    });
  },
  {
    // Deep watch the windows prop
    deep: true,
  },
);

// The state of the side panel windows
const state = ref<{
  [key: string]: SidepanelWindowState;
}>({});

// The total height of all windows
let totalHeight = 1;
let availableHeight = 1;
const growthTargets: string[] = [];
const shrinkTargets: string[] = [];

const headerSize = remToPx(2) + 1;

// The container element
const container = ref<HTMLElement | null>(null);
const containerSize = useElementSize(container);
watch(containerSize.height, onResize);

let lastDisabled = Date.now();
const disableAnimation = ref(true);

// The state of the mouse
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
  lastDisabled = Date.now();
  disableAnimation.value = false;

  if (state.value[id].minimized) {
    maximize(id);
  } else {
    minimize(id);
  }

  setTimeout(() => {
    if (Date.now() - lastDisabled >= 100) disableAnimation.value = true;
  }, 100);
}

/**
 * Event handler that handles changes in the window height, making sure that the windows do not take up more vertical
 * height than is visible.
 * @param height The height of the side panel after resizing.
 * @param oldHeight The height of the side panel before resizing.
 */
function onResize(height: number, oldHeight: number) {
  const growth = height - oldHeight;

  totalHeight += growth;
  availableHeight += growth;
  console.debug("Available height increased by ", growth);

  if (growth > 0) {
    growAnyTab(growth);
  } else {
    shrinkAnyTab(-growth);
  }

  mounted.value = true;
}

/**
 * Event handler that handles the resizing of the content of windows, used for setting the maximum height of windows.
 * @param id The window of which the content has been resized.
 * @param height The new size of the content.
 */
function onContentResize(id: string, height: number) {
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
  console.debug("Maximizing window", id);
  const tab = state.value[id];

  // Calculate the windows that are not minimized
  const openWindows = windows.value.filter((id) => !state.value[id].minimized);

  const allowedHeightShare = Math.round(totalHeight / (openWindows.length + 1));
  const desiredGrowth = Math.min(tab.maxContentHeight, allowedHeightShare);

  // Calculate the windows that are larger than the allowed height share
  const largeWindows: [string, number][] = openWindows.map((id) => [
    id,
    Math.max(state.value[id].height - allowedHeightShare, 0),
  ]);
  const available = largeWindows.reduce((acc, win) => (acc += win[1]), 0);

  const reduction = Math.min(available, Math.max(0, desiredGrowth - availableHeight));

  // Shrink the windows that are larger than the allowed height share
  if (available > 0) {
    for (const i in largeWindows) {
      const [tabId, exceededHeight] = largeWindows[i];
      const reduce = Math.round((exceededHeight / available) * reduction);
      shrinkTab(tabId, reduce);
    }
  }

  tab.minimized = false;

  // Grow the window to the desired height
  growTab(id, Math.max(desiredGrowth, availableHeight));
}

/**
 * Minimize a specific window.
 * @param id The id of the window to shrink.
 */
function minimize(id: string) {
  console.debug("Minimizing window", id);
  const tab = state.value[id];
  tab.minimized = true;

  const oldHeight = tab.height;
  // Shrink the window to the header size
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

  // Get the target window
  const tab = state.value[id];
  const canGrow = Math.min(availableHeight, headerSize + tab.maxContentHeight - tab.height);
  const actualGrowth = Math.min(px, canGrow);

  // Grow the window
  tab.height += actualGrowth;
  availableHeight -= actualGrowth;
  console.debug("Available height shrunk by ", actualGrowth);

  // Remove the target from the growth and shrink targets
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
  availableHeight += actualShrink;
  console.debug("Available height increased by ", actualShrink);

  removeTarget(id);
  // If the window is smaller than the header size, minimize it
  if (tab.height <= headerSize && !tab.minimized) {
    stopDragging();
    minimize(id);
  } else {
    // Else, add the target to the growth and shrink targets
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
  // Grow the windows
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
}

/**
 * Event handler for mouse movement.
 * @param event The MouseEvent to handle.
 */
function handleDragMovement(event: MouseEvent) {
  if (mouseState.dragging) {
    const growth = event.movementY;
    if (growth > 0) {
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
          <BaseContextMenu>
            <div
              @click="toggleTabSize(id)"
              class="left-0 z-10 flex w-full cursor-pointer justify-start space-x-1 whitespace-nowrap border-b p-1.5"
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
              class="z-0 -mt-px overflow-hidden border-t border-border duration-100"
              :style="{
                height: `${state[id].minimized ? '0px' : `${state[id].height - headerSize + 1}px`}`,
              }"
              :class="{
                'transition-all': !disableAnimation,
                'transition-none': disableAnimation,
              }"
            >
              <WindowPortalTarget
                ref="contentRefs"
                :window-id="id"
                @content-height="(entry) => onContentResize(id, entry)"
                :disallow-shrink="!disableAnimation"
                :area-height="state[id].height - headerSize"
              />
            </div>
            <template #menu>
              <ContextMenuRadioGroup :model-value="windowState[id].opened ? windowState[id].location : 'closed'">
                <ContextMenuRadioItem value="closed" @click="windowState[id].opened = false">
                  Closed
                </ContextMenuRadioItem>
                <ContextMenuRadioItem value="left" @click="windowState[id].location = 'left'">
                  Left sidepanel
                </ContextMenuRadioItem>
                <ContextMenuRadioItem value="right" @click="windowState[id].location = 'right'">
                  Right sidepanel
                </ContextMenuRadioItem>
                <ContextMenuSeparator />
                <ContextMenuItem @click="() => toggleTabSize(id)">
                  {{ state[id].minimized ? "Maximize" : "Minimize" }} window
                </ContextMenuItem>
              </ContextMenuRadioGroup>
            </template>
          </BaseContextMenu>
        </div>
        <div class="relative z-10 -mt-px border-b">
          <div
            class="absolute left-0 -mt-2 flex h-4 w-full cursor-ns-resize"
            @mousedown="startDragging(id)"
            v-if="!state[id].minimized"
          >
            <div class="my-2 h-0 w-full border-t" />
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
