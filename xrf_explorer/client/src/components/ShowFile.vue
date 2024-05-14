<script setup lang="ts">
import { computed } from 'vue'
import { useFetch } from '@vueuse/core';

// Fetch files
const { data } = useFetch(`/api/files`).get().json()
const files = computed(() => {
  return data.value as Array<string>;
})
</script>

<template>
  Uploaded files:
  <ul>
    <li v-for="file in files">
      {{ file }}
    </li>
  </ul>
</template>

<style scoped></style>
