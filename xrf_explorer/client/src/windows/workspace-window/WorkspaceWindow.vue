<script setup lang="ts">
import { Window } from "@/components/ui/window";
import { WorkspaceElementalCard, WorkspaceSpectralCard, WorkspaceImageCard } from ".";
import { appState } from "@/lib/app_state";
import { computed } from "vue";

const workspace = computed(() => appState.workspace);
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
