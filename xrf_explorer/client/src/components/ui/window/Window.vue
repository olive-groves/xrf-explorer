<script setup lang="ts">
import { Button } from '@/components/ui/button';
import { ChevronDownIcon, Cross2Icon } from "@radix-icons/vue";
import {
  Collapsible,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { CollapsibleContent } from "radix-vue";
import { Draggable } from "@/components/functional/draggable";
import { ScrollArea } from '@/components/ui/scroll-area';
import { inject, ref, toRef } from "vue";
import { window_state } from "./state";
import { useElementBounding, useWindowSize } from '@vueuse/core';
import { remToPx } from '@/lib/utils';

const handle = ref<HTMLElement | null>(null);
const container = inject<HTMLElement | null>("draggable_container")!;
const props = defineProps<{
  title: string,
  opened?: boolean,
  width?: number,
  height?: number,
  top?: number,
  left?: number,
  bottom?: number,
  right?: number
}>();

window_state[props.title] = {
  title: props.title,
  opened: props.opened
}

const state = toRef(window_state, props.title);

// TODO: Refactor into a separate component?
const windowSize = useWindowSize();
const initialW = props.width ?? 20;
const initialH = props.height ?? 15;
let initialX = remToPx(0.5);
if (props.left) { initialX = remToPx(props.left!) }
if (props.right) { initialX = windowSize.width.value - remToPx(props.right! + initialW) }
let initialY = remToPx(3.25);
if (props.top) { initialY = remToPx(props.top!) }
if (props.bottom) { initialY = windowSize.height.value - remToPx(props.bottom! + initialH) }
const containerSize = useElementBounding(container);
const content = ref<HTMLElement | null>(null);
const min_width = 12;
const maximized = ref(true);
</script>

<template>
  <Draggable :id="state.title" :container="container" :handle="handle" :class="{ hidden: !state.opened }" :x="initialX"
    :y="initialY">
    <Collapsible v-model:open="maximized" class="border rounded-lg bg-card overflow-hidden" :style="{
      'min-width':
        `${min_width}rem`, 'max-width': `${containerSize.width.value}px`, 'max-height':
        `${containerSize.height.value}px`,
    }">
      <div ref="handle" class="flex justify-between space-x-4 h-8 cursor-move transition-all duration-300">
        <div class="select-none font-bold flex items-center pl-2">
          {{ props.title }}
        </div>
        <div class="p-1">
          <CollapsibleTrigger>
            <Button variant="ghost" class="h-6 w-6 p-0">
              <ChevronDownIcon class="transition-transform duration-300" :class="{ 'rotate-180': maximized }" />
            </Button>
          </CollapsibleTrigger>
          <Button variant="ghost" @click="state.opened = false" class="h-6 w-6 p-0">
            <Cross2Icon />
          </Button>
        </div>
      </div>
      <CollapsibleContent force-mount class="max-h-full data-[state=closed]:hidden transition-all duration-300">
        <div ref="content" class="border-t resize overflow-hidden max-h-full" :style="{
          'min-width': `${min_width}rem`,
          'width': `${initialW}rem`,
          'height': `${initialH - 2}rem`
        }">
          <ScrollArea class="h-full">
            <div class="p-2">
              <slot />
            </div>
          </ScrollArea>
        </div>
      </CollapsibleContent>
    </Collapsible>
  </Draggable>
</template>