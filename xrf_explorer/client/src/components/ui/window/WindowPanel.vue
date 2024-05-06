<script setup lang="ts">
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { WindowPortalTarget } from '.';
import { ChevronRight } from 'lucide-vue-next';
import { ref } from 'vue';
import { window_state } from './state';
import { remToPx } from '@/lib/utils';

const props = defineProps<{
  windowId: string,
}>();

const state = window_state[props.windowId];

const isOpen = ref(true);

const height = ref(remToPx(10));
</script>

<template>
  <div @click="isOpen = !isOpen"
    class="w-full p-1 left-0 space-x-1 whitespace-nowrap flex items-center justify-start border-b">
    <ChevronRight class="h-5 w-5 min-w-5 transition-transform duration-200" :class="{
      'rotate-90': isOpen
    }" />
    <div class="font-bold">
      {{ state.title }}
    </div>
  </div>
  <div class="transition-all duration-200 overflow-hidden border-b -mt-px" :style="{
    height: `${isOpen ? height : 0}px`
  }">
    <div class="p-1 mt-px">
      <WindowPortalTarget :windowId="props.windowId" />
    </div>
  </div>
</template>