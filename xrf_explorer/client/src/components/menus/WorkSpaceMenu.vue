<script setup lang="ts">
import { MenubarContent, MenubarItem, MenubarMenu, MenubarTrigger } from "@/components/ui/menubar";
import { Dialog, DialogTrigger } from "@/components/ui/dialog";
import { ref } from "vue";
import { appState } from "@/lib/appState";
import { FileSetupDialog, ChannelSetupDialog } from "@/components/workspace";

// Dialog visibility variable
const dialogOpen = ref(false);

// Which window to open
const window = ref("");

// Reset the dialog state on close
function reset() {
  dialogOpen.value = false;
}
</script>

<template>
  <Dialog v-model:open="dialogOpen" @update:open="reset">
    <MenubarMenu>
      <MenubarTrigger
        v-tooltip="'toolbar.workspace'"
        v-if="appState.user.role === 'ADMIN' || appState.user.role === 'EDITOR'"
      >
        Workspace
      </MenubarTrigger>
      <MenubarTrigger v-else class="pointer-events-none w-full cursor-not-allowed opacity-50">
        Workspace
      </MenubarTrigger>
      <MenubarContent>
        <!-- Display setup workspace dialog and setup elemental channels dialog -->
        <DialogTrigger
          v-tooltip="'toolbar.setup_workspace'"
          v-if="(appState.user.role === 'ADMIN' || appState.user.role === 'EDITOR') && appState.workspace != undefined"
          class="w-full"
          @click="
            window = 'workspace';
            dialogOpen = true;
          "
        >
          <MenubarItem> Setup Workspace </MenubarItem>
        </DialogTrigger>
        <DialogTrigger v-else class="pointer-events-none w-full cursor-not-allowed opacity-50">
          <MenubarItem> Setup Workspace </MenubarItem>
        </DialogTrigger>
        <DialogTrigger
          v-tooltip="'toolbar.setup_elemental_channels'"
          v-if="(appState.user.role === 'ADMIN' || appState.user.role === 'EDITOR') && appState.workspace != undefined"
          class="w-full"
          @click="
            window = 'elementalChannels';
            dialogOpen = true;
          "
        >
          <MenubarItem> Setup Elemental Channels </MenubarItem>
        </DialogTrigger>
        <DialogTrigger v-else class="pointer-events-none w-full cursor-not-allowed opacity-50">
          <MenubarItem> Setup Elemental Channels </MenubarItem>
        </DialogTrigger>
      </MenubarContent>
    </MenubarMenu>

    <!-- Show the relevant window based on "window" -->
    <FileSetupDialog
      v-if="window == 'workspace' && appState.workspace != undefined"
      v-model="appState.workspace"
      @save="dialogOpen = false"
    />
    <ChannelSetupDialog
      v-if="window == 'elementalChannels' && appState.workspace != undefined"
      v-model="appState.workspace"
      @save="dialogOpen = false"
    />
  </Dialog>
</template>
