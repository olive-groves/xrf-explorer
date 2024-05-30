<script setup lang="ts">
import { WorkspaceElementalCard, WorkspaceSpectralCard, WorkspaceImageCard } from ".";
import { appState } from "@/lib/appState";
import { FrontendConfig } from "@/lib/config";
import { computed, inject, watch } from "vue";

const config = inject<FrontendConfig>("config")!;

const workspace = computed(() => appState.workspace);

/**
 * Update workspace on the backend whenever it gets changed.
 */
watch(
  workspace,
  (newWorkspace, oldWorkspace) => {
    // Make sure to not update the backend on initial load/final unload
    if (newWorkspace != undefined && oldWorkspace != undefined) {
      // Make sure to not update the backend when switching between data sources.
      if (newWorkspace.name == oldWorkspace.name) {
        console.info("Saving changes to workspace", newWorkspace.name);
        fetch(`${config.api.endpoint}/${newWorkspace.name}/workspace`, {
          method: "POST",
          body: JSON.stringify(newWorkspace),
          headers: {
            "Content-Type": "application/json",
          },
        });
      }
    }
  },
  { deep: true },
);
</script>

<template>
  <Window title="Workspace" location="left">
    <div class="space-y-2 p-2" v-if="workspace != undefined">
      <div>
        <div class="text-muted-foreground">Workspace name:</div>
        <div>{{ workspace.name }}</div>
      </div>
      <div>
        <div class="text-muted-foreground">Data sources:</div>
        <div class="space-y-2">
          <WorkspaceImageCard v-model="workspace.baseImage" base />
          <WorkspaceImageCard
            v-for="(_, index) in workspace.contextualImages"
            :key="index"
            v-model="workspace.contextualImages[index]"
          />
          <WorkspaceElementalCard
            v-for="(_, index) in workspace.elementalCubes"
            :key="index"
            v-model="workspace.elementalCubes[index]"
          />
          <WorkspaceSpectralCard
            v-for="(_, index) in workspace.spectralCubes"
            :key="index"
            v-model="workspace.spectralCubes[index]"
          />
        </div>
      </div>
    </div>
    <div v-else class="p-2">No workspace loaded, please use the file menu to load a workspace.</div>
  </Window>
</template>
