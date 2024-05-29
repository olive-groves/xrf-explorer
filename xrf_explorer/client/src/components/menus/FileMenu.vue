<script setup lang="ts">
import { computed, inject } from "vue";
import { useFetch } from "@vueuse/core";
import { MenubarItem } from "@/components/ui/menubar";
import { FrontendConfig } from "@/lib/config";
import { appState } from "@/lib/appState";

const config = inject<FrontendConfig>("config")!;

// Fetch files
const { data } = useFetch(`${config.api.endpoint}/datasources`).get().json();
const sources = computed(() => {
  return data.value as string[];
});

/**
 * Loads a workspace from the backend.
 * @param source - The source to load.
 */
async function loadWorkspace(source: string) {
  appState.workspace = await (await fetch(`${config.api.endpoint}/${source}/workspace`)).json();
  console.info(`Loading workspace ${source}`);
}
</script>

<template>
  <MenubarItem v-for="source in sources" :key="source" @click="() => loadWorkspace(source)">
    {{ source }}
  </MenubarItem>
</template>
