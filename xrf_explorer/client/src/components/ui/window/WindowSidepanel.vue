<script setup lang="ts">
import { SidepanelWindowState, windowState } from './state';
import { computed, ref, watch } from 'vue';
import { WindowPortalTarget } from '.';
import { ChevronRight } from 'lucide-vue-next';
import { remToPx } from '@/lib/utils';
import { useElementSize } from '@vueuse/core';

const props = defineProps<{
  windows: string[]
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
          maxContentHeight: 0
        }
      }
    });

    return props.windows;
  } else {
    return [];
  }
});

watch(windows, (newWindows, oldWindows) => {
  newWindows.forEach((id, index) => {
    if (state.value[id].height == 0) {
      // Perform setup
      console.debug("setting up");
      if (availableHeight < headerSize) {
        shrinkAnyTab(headerSize - availableHeight);
      }
      growTab(id, headerSize);
      removeTarget(id);

      // TODO: Fix maximizing upon setup
      // maximize(id);
    }

    // Update the index
    state.value[id].index = index;
  });
  oldWindows.forEach((id) => {
    if (!(newWindows.includes(id))) {
      // Clean up window properly
      console.debug("cleaning up", newWindows, oldWindows);
      if (id in state.value) {
        shrinkTab(id, state.value[id].height);
      }
    }
  });
}, {
  deep: true
})

const state = ref<{
  [key: string]: SidepanelWindowState
}>({})

let totalHeight = 1;
let availableHeight = 1;
const growthTargets: string[] = [];
const shrinkTargets: string[] = [];

const headerSize = remToPx(1.75) + 1;

const container = ref<HTMLElement | null>(null);
const containerSize = useElementSize(container);
watch(containerSize.height, onResize);

let disableAnimation = ref(false);

const mouseState: {
  handle: string,
  dragging: boolean
} = {
  handle: "",
  dragging: false
}

function toggleTabSize(id: string) {
  if (state.value[id].minimized) {
    maximize(id)
  } else {
    minimize(id)
  }
}

function onResize(height: number, oldHeight: number) {
  console.debug("onResize", height, oldHeight);
  const growth = height - oldHeight;

  totalHeight += growth;
  console.debug('Updating availableHeight', growth);
  availableHeight += growth;

  disableAnimation.value = true;
  if (growth > 0) {
    growAnyTab(growth)
  } else {
    shrinkAnyTab(-growth)
  }
  disableAnimation.value = false;

  console.debug("Indicating mount");
  mounted.value = true;
}

function onContentResize(id: string, height: number) {
  // Account for built in margin
  height += remToPx(0.5);

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

function maximize(id: string) {
  console.debug("maximize", id);
  const tab = state.value[id];

  const openWindows = windows.value.filter(id => !state.value[id].minimized);

  const allowedHeightShare = Math.round(totalHeight / (openWindows.length + 1))
  const desiredGrowth = Math.min(tab.maxContentHeight, allowedHeightShare);

  const largeWindows: [string, number][] = openWindows.map(id => [id, Math.max(state.value[id].height - allowedHeightShare, 0)]);
  const available = largeWindows.reduce((acc, win) => acc += win[1], 0);

  const reduction = Math.min(available, Math.max(0, desiredGrowth - availableHeight))

  console.debug(id, desiredGrowth, availableHeight, available, reduction);
  if (available > 0) {
    for (let i in largeWindows) {
      const [tabId, exceededHeight] = largeWindows[i];
      const reduce = Math.round((exceededHeight / available) * reduction);
      shrinkTab(tabId, reduce);
    }
  }

  tab.minimized = false;

  growTab(id, Math.max(desiredGrowth, availableHeight));
}

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

function growTab(id: string, px: number): number {
  console.debug(`Growing ${id} by ${px}px`)

  const tab = state.value[id];
  const canGrow = Math.min(availableHeight, headerSize + tab.maxContentHeight - tab.height);
  const actualGrowth = Math.min(px, canGrow);

  tab.height += actualGrowth;
  console.debug('Updating availableHeight', actualGrowth);
  availableHeight -= actualGrowth;

  removeTarget(id);
  console.debug(`Adding ${id} as target after growth`);
  growthTargets.unshift(id);
  shrinkTargets.push(id);
  return actualGrowth;
}

function shrinkTab(id: string, px: number): number {
  console.debug(`Shrinking ${id} by ${px}px`)

  const tab = state.value[id];
  const canShrink = tab.height - headerSize;
  const actualShrink = Math.min(px, canShrink);

  tab.height -= actualShrink;
  console.debug('Updating availableHeight', actualShrink);
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

function growAnyTab(px: number, from: number = -1): number {
  console.debug(`Growing any by ${px}px`)
  const targets = [...growthTargets].filter((id) => state.value[id].index > from);

  let remaining = px;
  for (let i = 0; i < targets.length; i++) {
    remaining -= growTab(targets[i], remaining);
    if (remaining <= 0) return px;
  }

  return px - remaining;
}

function shrinkAnyTab(px: number, from: number = -1): number {
  console.debug(`Shrinking any by ${px}px`)
  const targets = [...shrinkTargets].filter((id) => state.value[id].index > from);

  let remaining = px;
  for (let i = 0; i < targets.length; i++) {
    remaining -= shrinkTab(targets[i], remaining);
    if (remaining <= 0) return px;
  }

  return px - remaining;
}

function removeTarget(id: string) {
  console.debug(`Removing ${id} from targets`);
  if (growthTargets.includes(id)) {
    growthTargets.splice(growthTargets.indexOf(id), 1)
  }
  if (shrinkTargets.includes(id)) {
    shrinkTargets.splice(shrinkTargets.indexOf(id), 1)
  }
  console.debug(growthTargets, shrinkTargets);
}

function startDragging(handle: string) {
  mouseState.dragging = true;
  mouseState.handle = handle;
  disableAnimation.value = true;
}

function stopDragging() {
  mouseState.dragging = false;
  disableAnimation.value = false;
}

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
  <div ref="container" class="size-full" @mouseleave="stopDragging" @mouseup="stopDragging"
    @mousemove="handleDragMovement">
    <!-- TODO: Replace this calc with headerSize --->
    <div class="grid grid-cols-1 max-h-full"
      style="grid-template-rows: repeat(1, minmax(calc(1.75rem + 1px), max-content)) ">
      <template v-for="id in windows" :key="id">
        <div class="z-0 duration-100 overflow-hidden" :style="{
          height: `${state[id].height}px`,
        }" :class="{
          'transition-all': !disableAnimation
        }">
          <div @click="toggleTabSize(id)"
            class="w-full p-1 left-0 space-x-1 whitespace-nowrap flex items-center justify-start border-b cursor-pointer">
            <ChevronRight class="h-5 w-5 min-w-5 duration-100" :class="{
              'rotate-90': !state[id].minimized
            }" />
            <div class="font-bold">
              {{ state[id].title }}
            </div>
          </div>
          <div class="duration-100 overflow-hidden -mt-px" :style="{
            height: `${state[id].minimized ? '0px' : `${state[id].height - headerSize - 1}px`}`
          }" :class="{
            'transition-all': !disableAnimation
          }">
            <div class="p-1 mt-px">
              <WindowPortalTarget ref="contentRefs" :window-id="id"
                @contentHeight="(entry) => onContentResize(id, entry)"
                :area-height="state[id].height - headerSize - 1" />
            </div>
          </div>
        </div>
        <div v-if="!state[id].minimized" @mousedown="startDragging(id)" class="z-10 w-full h-2 -my-1 cursor-ns-resize">
          <div class="h-px bg-border mt-[calc(0.25rem-1px)]" />
        </div>
      </template>
    </div>
  </div>
</template>