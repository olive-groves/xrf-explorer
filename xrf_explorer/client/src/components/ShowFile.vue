<script setup lang="ts">
import { computed } from 'vue'
import { useFetch } from '@vueuse/core';

// Constants
const API_URL = 'http://localhost:8001/api'

// Fetch files
const { data } = useFetch(`${API_URL}/files`).get().json()
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
