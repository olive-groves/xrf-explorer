<script setup lang="ts">
import { computed } from 'vue';
import {
  Dialog,
  DialogContent
} from '.';
import { snakeCase } from 'change-case';
import { dialogState } from './state';

const props = defineProps<{
  id: string
}>();

const id = snakeCase(props.id);

if (!(id in dialogState)) {
  dialogState[id] = {
    open: false
  }
}

const isOpen = computed(() => {
  return dialogState[id].open;
});
</script>

<template>
  <Dialog :open="isOpen" @update:open="(val) => dialogState[id].open = val">
    <DialogContent>
      <slot />
    </DialogContent>
  </Dialog>
</template>