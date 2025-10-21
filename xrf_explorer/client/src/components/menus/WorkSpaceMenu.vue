<script setup lang="ts">
import { MenubarMenu, MenubarTrigger } from "@/components/ui/menubar";
import { Dialog } from "@/components/ui/dialog";
import { ref } from "vue";
import { appState } from "@/lib/appState";
import { FileSetupDialog } from "@/components/workspace";

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
            <MenubarTrigger v-if ="(appState.userRole === 'ADMIN' || appState.userRole === 'EDITOR') && appState.workspace != undefined" @click="window = 'workSpace'; dialogOpen = true;"> 
                WorkSpace 
            </MenubarTrigger>
        </MenubarMenu>

        <!-- Show the relevant window based on "window" -->
        <FileSetupDialog 
            v-if="window == 'workSpace' && appState.workspace != undefined" 
            v-model="appState.workspace"
            @save="dialogOpen = false" 
        />
    </Dialog>
</template>