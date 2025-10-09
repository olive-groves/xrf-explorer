<script setup lang="ts">
// Import the necessary components
import {
  MenubarContent,
  MenubarItem,
  MenubarMenu,
  MenubarRadioGroup,
  MenubarRadioItem,
  MenubarSeparator,
  MenubarTrigger,
  MenubarCheckboxItem
} from "@/components/ui/menubar";
import { Dialog, DialogTrigger } from "@/components/ui/dialog";
import { ResetClientDialog } from "@/components/workspace";
import { ref } from "vue";
import HelpDialog from "@/components/ui/help-menu/HelpDialog.vue";
import { helpState } from "@/lib/helpState";
// Import for the color mode
import { useColorMode } from "@vueuse/core";

// Dialog visibility variables
const dialogOpen = ref(false);
// Color mode variable
const colorMode = useColorMode({ emitAuto: true });

function toggleHelpDialogs() {
  helpState.enabled = !helpState.enabled;
}

</script>
<template>
  <Dialog v-model:open="dialogOpen">
    <MenubarMenu>
      <MenubarTrigger class="whitespace-nowrap font-bold"> XRF-Explorer </MenubarTrigger>
      <HelpDialog
        title="XRF Explorer Help Menu"
        text="The XRF Explorer menu provides access to external resources, theme/help menu settings, and the option to reset the client."
        :enabled="true"
      />
      <MenubarContent>
        <a href="https://github.com/olive-groves/xrf-explorer" target="_blank" rel="noopener noreferrer">
          <MenubarItem inset> Github </MenubarItem>
        </a>
        <a href="https://olive-groves.github.io/xrf-explorer" target="_blank" rel="noopener noreferrer">
          <MenubarItem inset> Code documentation </MenubarItem>
        </a>
        <a href="https://github.com/olive-groves/xrf-explorer-documentation" target="_blank" rel="noopener noreferrer">
          <MenubarItem inset> Technical documents </MenubarItem>
        </a>
        <MenubarSeparator />
        <MenubarRadioGroup v-model:model-value="colorMode">
          <MenubarRadioItem value="auto">Automatic mode</MenubarRadioItem>
          <MenubarRadioItem value="light">Light mode</MenubarRadioItem>
          <MenubarRadioItem value="dark">Dark mode</MenubarRadioItem>
        </MenubarRadioGroup>
        <MenubarSeparator />
        <MenubarCheckboxItem
          :checked="helpState.enabled"
          @click="toggleHelpDialogs"
        >
          Show Help Icons
        </MenubarCheckboxItem>
        <MenubarSeparator />
        <div class="flex items-center justify-between w-full">
          <DialogTrigger class="flex-grow">
            <MenubarItem inset>Reset client</MenubarItem>
          </DialogTrigger>
          <HelpDialog
            title="Reset Client Help Menu"
            text="The Reset client resets the application view to default settings."
            :enabled="true"
          />
        </div>
      </MenubarContent>
    </MenubarMenu>
    <ResetClientDialog @close="dialogOpen = false" />
  </Dialog>
</template>