<script setup lang="ts">
import { MenubarContent, MenubarItem, MenubarMenu, MenubarTrigger } from "@/components/ui/menubar";
import { Dialog, DialogTrigger } from "@/components/ui/dialog";
import { computed, ref, watch, inject } from "vue";
import { appState, datasource } from "@/lib/appState";
import { FileSetupDialog, ChannelSetupDialog } from "@/components/workspace";
import { deepClone } from "@/lib/utils";
import { FrontendConfig } from "@/lib/config";
import { toast } from "vue-sonner";

// Inject the frontend configuration
const config = inject<FrontendConfig>("config")!;

// Which window to open
const window = ref("");

// Dialog visibility variable
const dialogOpen = ref(false);

// Define the workspace model
const workspace = computed(() => appState.workspace);

// Create a local copy of the workspace
const localWorkspace = ref(workspace.value == undefined ? undefined : deepClone(workspace.value));

/**
 * Update local workspace when switching between workspaces.
 */
watch(datasource, () => {
  localWorkspace.value = deepClone(workspace.value);
});

/**
 * Open file dialog with fresh workspace data.
 */
function openFileDialog() {
  console.log("openFileDialog called, workspace.value:", workspace.value);
  if (!workspace.value) {
    console.error("Cannot open file dialog: workspace is undefined");
    return;
  }
  const cloned = deepClone(workspace.value);
  // Ensure partial arrays exist (for older workspaces that don't have them)
  if (!cloned.partialSpectralCubes) cloned.partialSpectralCubes = [];
  if (!cloned.partialElementalCubes) cloned.partialElementalCubes = [];
  localWorkspace.value = cloned;
  console.log("localWorkspace after sync:", localWorkspace.value);
  window.value = "workspace";
  dialogOpen.value = true;
}

/**
 * Open channels dialog with fresh workspace data.
 */
function openChannelsDialog() {
  if (!workspace.value) return;
  localWorkspace.value = deepClone(workspace.value);
  window.value = "elementalChannels";
  dialogOpen.value = true;
}

/**
 * Update the workspace persistently.
 */
function updateWorkspace() {
  // deepClone the local workspace to avoid reactivity issues
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
      window.value = "";
      dialogOpen.value = false;
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

/**
 * Reset the dialog state when closed.
 */
function reset() {
  window.value = "";
  localWorkspace.value = deepClone(workspace.value);
}
</script>

<template>
  <Dialog v-model:open="dialogOpen" @update:open="reset">
    <MenubarMenu>
      <MenubarTrigger
        v-tooltip="'toolbar.workspace'"
        v-if="(appState.user.role === 'ADMIN' || appState.user.role === 'EDITOR') && appState.workspace"
      >
        Workspace
      </MenubarTrigger>
      <MenubarTrigger
        class="w-full cursor-not-allowed opacity-50"
        v-tooltip="'toolbar.workspace_not_loaded'"
        v-if="(appState.user.role === 'ADMIN' || appState.user.role === 'EDITOR') && !appState.workspace"
      >
        Workspace
      </MenubarTrigger>
      <MenubarContent v-if="appState.workspace">
        <!-- Display setup workspace dialog and setup elemental channels dialog -->
        <DialogTrigger
          v-tooltip="'toolbar.setup_workspace'"
          v-if="appState.user.role === 'ADMIN' || appState.user.role === 'EDITOR'"
          class="w-full"
          @click="openFileDialog"
        >
          <MenubarItem> Setup Workspace </MenubarItem>
        </DialogTrigger>
        <DialogTrigger
          v-tooltip="'toolbar.setup_elemental_channels'"
          v-if="appState.user.role === 'ADMIN' || appState.user.role === 'EDITOR'"
          class="w-full"
          @click="openChannelsDialog"
        >
          <MenubarItem> Setup Elemental Channels </MenubarItem>
        </DialogTrigger>
      </MenubarContent>
    </MenubarMenu>

    <!-- Show the relevant window based on "window" -->
    <FileSetupDialog
      v-if="window == 'workspace' && localWorkspace != undefined"
      v-model="localWorkspace"
      @save="
        updateWorkspace();
        dialogOpen = false;
      "
    />
    <ChannelSetupDialog
      v-if="window == 'elementalChannels' && localWorkspace != undefined"
      v-model="localWorkspace"
      @save="
        updateWorkspace();
        dialogOpen = false;
      "
    />
  </Dialog>
</template>
