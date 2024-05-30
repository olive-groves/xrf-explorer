<script setup lang="ts">
import { MenubarMenu, MenubarTrigger, MenubarContent, MenubarItem } from "@/components/ui/menubar";
</script>

<template>
  <MenubarMenu>
    <MenubarTrigger> Export </MenubarTrigger>
    <MenubarContent>
      <MenubarItem> Main viewer </MenubarItem>
      <MenubarItem> Elemental composition </MenubarItem>
      <MenubarItem> Spectrum </MenubarItem>
      <MenubarItem> Dimensionality reduction </MenubarItem>
    </MenubarContent>
  </MenubarMenu>
</template>
