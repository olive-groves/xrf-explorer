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
import { useColorMode } from "@vueuse/core";
import { resetWindow } from "@/lib/utils";

const colorMode = useColorMode({ emitAuto: true });
</script>

<template>
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
      <MenubarItem @click="resetWindow">Reset client</MenubarItem>
    </MenubarContent>
  </MenubarMenu>
</template>
