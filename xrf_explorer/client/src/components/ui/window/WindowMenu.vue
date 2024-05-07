<script setup lang="ts">
import {
  MenubarCheckboxItem,
  MenubarContent,
  MenubarMenu,
  MenubarTrigger,
  MenubarSeparator
} from '@/components/ui/menubar'
import { windowState } from './state';
import { computed, useSlots } from 'vue';

const slots = useSlots();
const hasSlot = computed(() => {
  return ('default' in slots);
})
</script>

<template>
  <MenubarMenu>
    <MenubarTrigger>
      View
    </MenubarTrigger>
    <MenubarContent>
      <MenubarCheckboxItem v-for="window in windowState" v-model:checked="window.opened">
        {{ window.title }}
      </MenubarCheckboxItem>
      <MenubarSeparator v-if="hasSlot" />
      <slot />
    </MenubarContent>
  </MenubarMenu>
</template>