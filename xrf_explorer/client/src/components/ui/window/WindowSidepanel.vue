<script setup lang="ts">
import { WindowPanel } from '.';
import { window_state } from './state';
</script>

<template>
  <div class="grid grid-cols-1 max-h-full"
    style="grid-template-rows: repeat(1, minmax(calc(1.75rem + 1px), max-content)) ">
    <template v-for="window in window_state">
      <WindowPanel :key="window.id" :window-id="window.id" v-if="window.opened" />
    </template>
  </div>
</template>