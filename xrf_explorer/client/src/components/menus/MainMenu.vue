<script setup lang="ts">
import {
  MenubarContent,
  MenubarItem,
  MenubarMenu,
  MenubarRadioGroup,
  MenubarRadioItem,
  MenubarSeparator,
  MenubarTrigger,
} from "@/components/ui/menubar";
import { Dialog, DialogTrigger } from "@/components/ui/dialog";
import { ResetClientDialog } from "@/components/workspace";
import { ref } from "vue";
import { useColorMode } from "@vueuse/core";

const dialogOpen = ref(false);
const colorMode = useColorMode({ emitAuto: true });
</script>

<template>
  <Dialog v-model:open="dialogOpen">
    <MenubarMenu>
      <MenubarTrigger class="whitespace-nowrap font-bold"> XRF-Explorer </MenubarTrigger>
      <MenubarContent>
        <a href="https://github.com/olive-groves/xrf-explorer" target="_blank" rel="noopener noreferrer">
          <MenubarItem> Github </MenubarItem>
        </a>
        <a href="https://github.com/olive-groves/xrf-explorer" target="_blank" rel="noopener noreferrer">
          <MenubarItem> Documentation </MenubarItem>
        </a>
        <MenubarSeparator />
        <MenubarRadioGroup v-model:model-value="colorMode">
          <MenubarRadioItem value="auto">Automatic mode</MenubarRadioItem>
          <MenubarRadioItem value="light">Light mode</MenubarRadioItem>
          <MenubarRadioItem value="dark">Dark mode</MenubarRadioItem>
        </MenubarRadioGroup>
        <MenubarSeparator />
        <DialogTrigger class="w-full"><MenubarItem>Reset client</MenubarItem></DialogTrigger>
      </MenubarContent>
    </MenubarMenu>
    <ResetClientDialog @close="dialogOpen = false" />
  </Dialog>
</template>
