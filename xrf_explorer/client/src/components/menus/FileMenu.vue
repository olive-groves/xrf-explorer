<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useFetch } from '@vueuse/core';

import { DialogMenuItem } from '@/components/ui/dialog';

import frontendConfig from '../../.././public/frontend.json';

const { 'api-url': API_URL } = frontendConfig;
console.log(API_URL);

// Fetch files
const { data } = useFetch(`${API_URL}/available_data_sources`).get().json();
const files = computed(() => {
  return data.value as Array<string>;
})

</script>

<template>
  <DialogMenuItem v-for="file in files" :key="file" :id="`open_file_${file}`">
    {{ file }}
  </DialogMenuItem>
</template>