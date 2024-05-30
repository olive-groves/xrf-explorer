<script setup lang="ts">
import {
  MenubarContent,
  MenubarItem,
  MenubarMenu,
  MenubarSeparator,
  MenubarSub,
  MenubarSubContent,
  MenubarSubTrigger,
  MenubarTrigger,
} from "@/components/ui/menubar";
import { useColorMode } from "@vueuse/core";
import { inject } from "vue";
import { FrontendConfig } from "@/lib/config";

const config = inject<FrontendConfig>("config")!;
const colorMode = useColorMode({
  initialValue: config.defaultTheme,
});
</script>

<template>
  <MenubarMenu>
    <MenubarTrigger class="whitespace-nowrap font-bold"> XRF-Explorer </MenubarTrigger>
    <MenubarContent>
      <MenubarItem> Github </MenubarItem>
      <MenubarSeparator />
      <MenubarItem> Preferences </MenubarItem>
      <MenubarSub>
        <MenubarSubTrigger> Theme </MenubarSubTrigger>
        <MenubarSubContent>
          <MenubarItem @click="colorMode = 'light'"> Light mode </MenubarItem>
          <MenubarItem @click="colorMode = 'dark'"> Dark mode </MenubarItem>
        </MenubarSubContent>
      </MenubarSub>
      <MenubarSeparator />
      <MenubarItem> Documentation </MenubarItem>
    </MenubarContent>
  </MenubarMenu>
</template>
