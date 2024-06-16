<script setup lang="ts">
import { computed, h, inject, markRaw, ref } from "vue";
import { useFetch } from "@vueuse/core";
import { MenubarMenu, MenubarTrigger, MenubarContent, MenubarSeparator, MenubarItem } from "@/components/ui/menubar";
import { Dialog, DialogTrigger } from "@/components/ui/dialog";
import { FrontendConfig } from "@/lib/config";
import { appState } from "@/lib/appState";
import { toast } from "vue-sonner";
import { CreateWorkspaceDialog } from "@/components/workspace";

const config = inject<FrontendConfig>("config")!;

// Fetch files
const request = useFetch(`${config.api.endpoint}/datasources`);
const sources = computed(() => {
  return JSON.parse((request.data.value ?? "[]") as string) as string[];
});

const dialogOpen = ref(false);

/**
 * Loads a workspace from the backend.
 * @param source - The source to load.
 */
function loadWorkspace(source: string) {
  fetch(`${config.api.endpoint}/${source}/workspace`).then(
    async (value) => {
      value.json().then(
        (workspace) => {
          toast.info(`Loading workspace ${source}`, {
            description: "This may take a couple of minutes",
          });
          console.info(`Loading workspace ${source}`);
          appState.workspace = workspace;
        },
        () =>
          toast.error(`Failed to load workspace ${source}`, {
            description: markRaw(h("div", [h("code", "workspace.json"), " might be missing or malformed"])),
          }),
      );
    },
    () =>
      toast.error(`Failed to load workspace ${source}`, {
        description: markRaw(h("div", [h("code", "workspace.json"), " might be missing or malformed"])),
      }),
  );
}
</script>

<template>
  <Dialog v-model:open="dialogOpen">
    <MenubarMenu>
      <MenubarTrigger @click="() => request.execute()"> File </MenubarTrigger>
      <MenubarContent>
        <DialogTrigger class="w-full"><MenubarItem>New data source</MenubarItem></DialogTrigger>
        <MenubarSeparator />
        <MenubarItem disabled v-if="sources.length <= 0">No data sources available</MenubarItem>
        <MenubarItem v-for="source in sources" :key="source" @click="() => loadWorkspace(source)">
          {{ source }}
        </MenubarItem>
      </MenubarContent>
    </MenubarMenu>
    <CreateWorkspaceDialog @close="dialogOpen = false" />
  </Dialog>
</template>
