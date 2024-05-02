<script setup lang="ts">
import {
  MenubarCheckboxItem,
  MenubarContent,
  MenubarMenu,
  MenubarTrigger,
} from '@/components/ui/menubar'
import { window_state } from './state';
</script>

<template>
  <MenubarMenu>
    <MenubarTrigger>
      View
    </MenubarTrigger>
    <MenubarContent>
      <MenubarCheckboxItem v-for="window in window_state" v-model:checked="window.opened">
        {{ window.title }}
      </MenubarCheckboxItem>
    </MenubarContent>
  </MenubarMenu>
</template>