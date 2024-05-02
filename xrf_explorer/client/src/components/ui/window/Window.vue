<script setup lang="ts">
import { ChevronDownIcon, Cross2Icon } from "@radix-icons/vue";

import { computed, ref } from "vue";
import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { clamp, useDraggable, useElementBounding, useParentElement } from "@vueuse/core";
import { window_state } from "@/components/ui/window/state";

const props = withDefaults(defineProps<{
  id: string,
  title: string;
  opened?: boolean;
  closed_width?: number;
  width?: number;
}>(), {
  closed_width: 18,
  width: 25,
  opened: false
});

if (props.id == undefined) {
  throw new Error("Window ID must be defined")
}

window_state.windows[props.id] = {
  is_opened: props.opened,
  z_index: 0
};

const isOpen = computed(() => {
  return window_state.windows[props.id].is_opened;
});
const zIndex = computed(() => {
  return window_state.windows[props.id].z_index;
})
const isMaximized = ref(true);

const container = useParentElement();
const draggable = ref<HTMLElement | null>(null);
const handle = ref<HTMLElement | null>(null);

const { left, right, top, bottom } = useElementBounding(container);
const { width, height } = useElementBounding(draggable);

const { x, y } = useDraggable(draggable, {
  handle: handle,
  initialValue: {
    x: 20,
    y: 52.5,
  },
});

const restrictedX = computed(() =>
  clamp(left.value, x.value, right.value - width.value)
);
const restrictedY = computed(() =>
  clamp(top.value, y.value, bottom.value - height.value)
);

function moveForwards() {
  let count = Object.keys(window_state.windows).length;
  for (let window in window_state.windows) {
    if (window_state.windows[window].z_index > window_state.windows[props.id].z_index) {
      window_state.windows[window].z_index--;
    }
  }
  window_state.windows[props.id].z_index = count - 1;
}
</script>

<template>
  <div ref="draggable" class="fixed rounded-xl border bg-card text-card-foreground shadow select-none" :style="{
    top: `${restrictedY}px`,
    left: `${restrictedX}px`,
    'z-index': zIndex
  }" :class="{ 'hidden': !isOpen }" @mousedown="moveForwards()">
    <Collapsible v-model:open="isMaximized" class="transition-all duration-300"
      :style="{ 'width': isMaximized ? props.width + 'em' : props.closed_width + 'em' }">
      <div ref="handle" class="p-2 cursor-move flex items-center justify-between space-x-4">
        <div class="font-bold select-none">
          {{ props.title }}
        </div>
        <div>
          <CollapsibleTrigger>
            <Button variant="ghost" class="h-6 w-6 p-0">
              <ChevronDownIcon class="transition-all duration-300" :class="{ 'rotate-180': isMaximized }" />
            </Button>
          </CollapsibleTrigger>
          <Button variant="ghost" class="h-6 w-6 p-0" @click="window_state.windows[id].is_opened = false">
            <Cross2Icon />
          </Button>
        </div>
      </div>
      <CollapsibleContent>
        <div class="border-t p-2 overflow-hidden" :style="{ 'width': props.width + 'em' }">
          <slot />
        </div>
      </CollapsibleContent>
    </Collapsible>
  </div>
</template>
