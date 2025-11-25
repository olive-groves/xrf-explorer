<script setup lang="ts">
import { computed, h, inject, markRaw, ref } from "vue";
import { useFetch } from "@vueuse/core";
import { MenubarMenu, MenubarTrigger, MenubarContent, MenubarSeparator, MenubarItem } from "@/components/ui/menubar";
import { Dialog, DialogTrigger } from "@/components/ui/dialog";
import { FrontendConfig } from "@/lib/config";
import { appState } from "@/lib/appState";
import { toast } from "vue-sonner";
import { CreateWorkspaceDialog } from "@/components/workspace";

// Inject the frontend configuration
const config = inject<FrontendConfig>("config")!;

// Fetch files
const request = useFetch(`${config.api.endpoint}/data_sources`);
const sources = computed(() => {
  return JSON.parse((request.data.value ?? "[]") as string) as string[];
});

// Reactive filtered sources
const filteredSources = computed(() => {
  // Admins can see all sources
  if (appState.user.role === "ADMIN") {
    return sources.value;
  }
  const userProjects = appState.user.projects ?? [];
  return sources.value.filter((source) => userProjects.includes(source));
});

// Dialog visibility variable
const dialogOpen = ref(false);

/**
 * Loads a workspace from the backend.
 * @param source - The source to load.
 */
function loadWorkspace(source: string) {
  // Prevent loading if the user does not have access
  if (appState.user.projects.includes(source) === false && appState.user.role !== "ADMIN") {
    toast.error(`You do not have permission to access project ${source}`);
    return;
  }
  const errorMsg = {
    message: `Failed to load workspace ${source}`,
    data: {
      description: markRaw(h("div", [h("code", "workspace.json"), " might be missing or malformed"])),
    },
  };

  fetch(`${config.api.endpoint}/${source}/workspace`).then(
    async (value) => {
      value.json().then(
        // Load the workspace
        (workspace) => {
          toast.info(`Loading workspace ${source}`, {
            description: "This may take a couple of minutes",
          });
          // Update the app state
          console.info(`Loading workspace ${source}`);
          appState.workspace = workspace;
        },
        () => toast.error(errorMsg.message, errorMsg.data),
      );
    },
    () => toast.error(errorMsg.message, errorMsg.data),
  );
}
</script>

<template>
  <Dialog v-model:open="dialogOpen">
    <MenubarMenu>
      <MenubarTrigger @click="() => request.execute()" title="Manage projects"> File </MenubarTrigger>
      <MenubarContent>
        <!-- Only show new project button for admins and editors -->
        <DialogTrigger v-if="appState.user.role === 'ADMIN' || appState.user.role === 'EDITOR'" class="w-full"
          ><MenubarItem>New project</MenubarItem>
        </DialogTrigger>
        <MenubarItem
          v-if="appState.user.role === 'ADMIN' || appState.user.role === 'EDITOR'"
          @click="
            () => {
              if (appState.workspace) {
                appState.workspace.stitchingMode = appState.workspace.stitchingMode === 'partial' ? 'full' : 'partial';
              }
            }
          "
        >
          {{ "Stitch" }}
        </MenubarItem>
        <MenubarSeparator v-if="appState.user.role === 'ADMIN' || appState.user.role === 'EDITOR'" />
        <MenubarItem disabled v-if="filteredSources.length <= 0">No projects available</MenubarItem>
        <MenubarItem v-for="source in filteredSources" :key="source" @click="() => loadWorkspace(source)">
          {{ source }}
        </MenubarItem>
      </MenubarContent>
    </MenubarMenu>
    <CreateWorkspaceDialog @close="dialogOpen = false" />
  </Dialog>
</template>
