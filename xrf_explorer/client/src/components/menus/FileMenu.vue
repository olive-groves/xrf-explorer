<script setup lang="ts">
import { computed, inject } from "vue";
import { useFetch } from "@vueuse/core";
import { MenubarMenu, MenubarTrigger, MenubarContent, MenubarSeparator, MenubarItem } from "@/components/ui/menubar";
import { DialogMenuItem } from "@/components/ui/dialog";
import { FrontendConfig } from "@/lib/config";
import { appState } from "@/lib/appState";
import { titleCase } from "title-case";

const config = inject<FrontendConfig>("config")!;

// Fetch files
const request = useFetch(`${config.api.endpoint}/datasources`);
const sources = computed(() => {
  return JSON.parse((request.data.value ?? "[]") as string) as string[];
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
  <MenubarMenu>
    <MenubarTrigger @click="() => request.execute()"> File </MenubarTrigger>
    <MenubarContent>
      <DialogMenuItem id="upload_file"> Upload files </DialogMenuItem>
      <MenubarSeparator />
      <MenubarItem disabled v-if="sources.length <= 0">No data sources available</MenubarItem>
      <MenubarItem v-for="source in sources" :key="source" @click="() => loadWorkspace(source)">
        {{ titleCase(source) }}
      </MenubarItem>
    </MenubarContent>
  </MenubarMenu>
</template>
