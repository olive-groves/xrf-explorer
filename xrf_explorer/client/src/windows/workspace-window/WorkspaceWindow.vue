<script setup lang="ts">
import { Dialog } from "@/components/ui/dialog";
import { DeleteWorkspaceDialog, WorkspaceCard } from ".";
import { Atom, AudioWaveform, Image, ImagePlus, Layers3 } from "lucide-vue-next";
import { appState, datasource } from "@/lib/appState";
import { FrontendConfig } from "@/lib/config";
import { computed, inject, ref, watch } from "vue";
import { toast } from "vue-sonner";
import { ChannelSetupDialog, FileSetupDialog } from "@/components/workspace";
import { deepClone } from "@/lib/utils";

const config = inject<FrontendConfig>("config")!;

const workspace = computed(() => appState.workspace);

const localWorkspace = ref(workspace.value == undefined ? undefined : deepClone(workspace.value));

/**
 * Update local workspace when switching between workspaces.
 */
watch(datasource, () => {
  localWorkspace.value = deepClone(workspace.value);
});

const fileDialog = ref(false);
const channelsDialog = ref(false);
const deletionDialog = ref(false);

/**
 * Update the workspace persistently.
 */
function updateWorkspace() {
  const newWorkspace = deepClone(localWorkspace.value!);
  console.info("Saving changes to workspace", newWorkspace);

  // Send a POST request to update the workspace
  fetch(`${config.api.endpoint}/${newWorkspace.name}/workspace`, {
    method: "POST",
    body: JSON.stringify(newWorkspace),
    headers: {
      "Content-Type": "application/json",
    },
  }).then(
    () => {
      // If the request is successful, update the app state and display a success message
      appState.workspace = newWorkspace;
      fileDialog.value = false;
      channelsDialog.value = false;
      toast.success("Updated workspace", {
        description: "The updates are persistent between sessions",
      });
    },
    () => {
      // If the request fails, display a warning message
      toast.warning("Failed to update workspace", {
        description: "No changes have been made",
      });
    },
  );
}
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
          <WorkspaceCard :name="workspace.baseImage.name" description="Base image" @settings="fileDialog = true">
            <template #icon><Image class="size-full" /></template>
          </WorkspaceCard>
          <WorkspaceCard
            v-for="image in workspace.contextualImages"
            :key="image.name"
            :name="image.name"
            description="Contextual image"
            @settings="fileDialog = true"
          >
            <template #icon><ImagePlus class="size-full" /></template>
          </WorkspaceCard>
          <WorkspaceCard
            v-for="cube in workspace.spectralCubes"
            :key="cube.name"
            :name="cube.name"
            description="Spectral cube"
            @settings="fileDialog = true"
          >
            <template #icon><AudioWaveform class="size-full" /></template>
          </WorkspaceCard>
          <WorkspaceCard
            v-for="cube in workspace.elementalCubes"
            :key="cube.name"
            :name="cube.name"
            description="Elemental cube"
            @settings="fileDialog = true"
          >
            <template #icon><Atom class="size-full" /></template>
          </WorkspaceCard>
          <WorkspaceCard
            name="Elemental channels"
            description="Generated data"
            @settings="channelsDialog = true"
            v-if="workspace.elementalCubes.length > 0"
          >
            <template #icon><Layers3 class="size-full" /></template>
          </WorkspaceCard>
        </div>
      </div>
      <Button variant="destructive" @click="deletionDialog = true"> Delete project </Button>
      <Dialog v-model:open="deletionDialog">
        <DeleteWorkspaceDialog :name="workspace.name" @close="deletionDialog = false" />
      </Dialog>
      <Dialog v-model:open="fileDialog">
        <FileSetupDialog v-model="localWorkspace" @save="updateWorkspace" />
      </Dialog>
      <Dialog v-model:open="channelsDialog">
        <ChannelSetupDialog v-model="localWorkspace" @save="updateWorkspace" />
      </Dialog>
    </div>
  </Window>
</template>
