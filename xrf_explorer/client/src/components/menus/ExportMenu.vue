<script setup lang="ts">
import { MenubarMenu, MenubarTrigger, MenubarContent, MenubarItem } from "@/components/ui/menubar";
import { exportToImage, exportableElements } from "@/lib/export";
import { sentenceCase, snakeCase } from "change-case";
</script>

<template>
  <MenubarMenu>
    <MenubarTrigger> Export </MenubarTrigger>
    <MenubarContent>
      <MenubarItem disabled v-if="Object.keys(exportableElements).length <= 0">Nothing to export</MenubarItem>
      <MenubarItem
        v-for="name in Object.keys(exportableElements)"
        :key="name"
        @click="() => exportToImage(snakeCase(name), exportableElements[name])"
      >
        {{ sentenceCase(name) }}
      </MenubarItem>
    </MenubarContent>
  </MenubarMenu>
</template>
