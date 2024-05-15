<script setup lang="ts">
import { computed, inject } from "vue";
import { useFetch } from "@vueuse/core";
import { DialogMenuItem } from "@/components/ui/dialog";
import { FrontendConfig } from "@/lib/config";

const config = inject<FrontendConfig>("config")!;

// Fetch files
const { data } = useFetch(`${config.api.endpoint}/available_data_sources`).get().json();
const files = computed(() => {
  return data.value as Array<string>;
});
</script>

<template>
  <DialogMenuItem v-for="file in files" :key="file" :id="`open_file_${file}`">
    {{ file }}
  </DialogMenuItem>
</template>
