<script setup lang="ts">
import { MenubarMenu, MenubarTrigger, MenubarContent, MenubarItem } from "@/components/ui/menubar";
</script>

<template>
  <MenubarMenu>
    <MenubarTrigger> Export </MenubarTrigger>
    <MenubarContent>
      <MenubarItem> Main viewer image</MenubarItem>
      <MenubarItem> Elemental composition visualization</MenubarItem>
      <MenubarItem> Spectral visualization </MenubarItem>
      <MenubarItem> Dimensionality reduction visualization</MenubarItem>
      <MenubarItem> Context visualization </MenubarItem>
    </MenubarContent>
  </MenubarMenu>
</template>
