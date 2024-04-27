<script setup lang="ts">
import { ref, provide } from 'vue';

const container = ref<HTMLElement | null>(null);

provide("window_container", container);
</script>

<template>
  <div ref="container">
    <slot />
  </div>
</template>